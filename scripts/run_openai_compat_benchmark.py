"""Micro benchmark for OpenAI-compatible gateway hot paths and mixed-load stress."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from app.main import app
from app.memory import ledger as memory_ledger


DEFAULT_JSON_OUT = Path("output/benchmarks/openai-compat-benchmark.json")


@dataclass(frozen=True, slots=True)
class MetricSummary:
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float

    def as_dict(self) -> dict[str, float]:
        return {
            "mean_ms": self.mean_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
        }


@dataclass(slots=True)
class MixedWorkerResult:
    chat_stream_ms: list[float]
    responses_stream_ms: list[float]
    chat_non_stream_ms: list[float]
    embeddings_ms: list[float]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark OpenAI-compatible gateway performance.")
    parser.add_argument("--chat-runs", type=int, default=250)
    parser.add_argument("--responses-runs", type=int, default=250)
    parser.add_argument("--embeddings-runs", type=int, default=250)
    parser.add_argument("--models-runs", type=int, default=200)
    parser.add_argument("--warmup-runs", type=int, default=12)

    parser.add_argument("--mixed-workers", type=int, default=8)
    parser.add_argument("--mixed-cycles", type=int, default=20)
    parser.add_argument("--long-prompt-chars", type=int, default=6000)
    parser.add_argument("--embedding-batch-size", type=int, default=64)
    parser.add_argument("--embedding-text-chars", type=int, default=512)
    parser.add_argument("--skip-mixed", action="store_true")

    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * ratio) - 1))
    return ordered[idx]


def _round3(value: float) -> float:
    return round(value, 3)


def _summarize(values: list[float]) -> MetricSummary:
    if not values:
        return MetricSummary(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return MetricSummary(
        mean_ms=_round3(sum(values) / len(values)),
        p50_ms=_round3(_percentile(values, 0.50)),
        p95_ms=_round3(_percentile(values, 0.95)),
        p99_ms=_round3(_percentile(values, 0.99)),
        min_ms=_round3(min(values)),
        max_ms=_round3(max(values)),
    )


def _measure_one_call_ms(fn: Callable[[], None]) -> float:
    start_ns = time.perf_counter_ns()
    fn()
    end_ns = time.perf_counter_ns()
    return (end_ns - start_ns) / 1_000_000.0


def _measure_ms(fn: Callable[[], None], runs: int) -> list[float]:
    samples: list[float] = []
    append_sample = samples.append
    for _ in range(max(1, runs)):
        append_sample(_measure_one_call_ms(fn))
    return samples


def _consume_stream_lines(response) -> None:
    for _ in response.iter_lines():
        pass


def _build_long_prompt(target_chars: int) -> str:
    target = max(512, target_chars)
    block = (
        "project status checkpoint: decision keep api stable; "
        "risk migration drift under mixed traffic; "
        "todo add stream benchmark and p99 guardrail; "
        "constraint avoid provider lock-in and keep fallback path deterministic. "
    )
    parts: list[str] = []
    total = 0
    index = 0
    while total < target:
        part = f"[{index}] {block}"
        parts.append(part)
        total += len(part)
        index += 1
    return "".join(parts)


def _build_embedding_inputs(batch_size: int, text_chars: int) -> list[str]:
    size = max(1, batch_size)
    target = max(64, text_chars)
    block = (
        "context ledger embedding stress text with deterministic content and "
        "minor variant for stable benchmark behavior "
    )

    items: list[str] = []
    append_item = items.append
    for idx in range(size):
        segments: list[str] = [f"item-{idx} "]
        total = len(segments[0])
        inner = 0
        while total < target:
            segment = f"{block}{inner} "
            segments.append(segment)
            total += len(segment)
            inner += 1
        append_item("".join(segments))
    return items


def _chat_non_stream(
    client: TestClient,
    *,
    message_text: str,
    project_id: str,
    session_id: str,
    model: str,
    max_tokens: int,
) -> None:
    response = client.post(
        "/openai/v1/chat/completions",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are concise."},
                {"role": "user", "content": message_text},
            ],
            "stream": False,
            "project_id": project_id,
            "session_id": session_id,
            "max_tokens": max_tokens,
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"chat non-stream failed: {response.status_code} {response.text}")
    _ = response.json()


def _chat_stream(
    client: TestClient,
    *,
    message_text: str,
    project_id: str,
    session_id: str,
    model: str,
    max_tokens: int,
) -> None:
    with client.stream(
        "POST",
        "/openai/v1/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": message_text}],
            "stream": True,
            "project_id": project_id,
            "session_id": session_id,
            "max_tokens": max_tokens,
        },
    ) as response:
        if response.status_code != 200:
            raise RuntimeError(f"chat stream failed: {response.status_code} {response.text}")
        _consume_stream_lines(response)


def _responses_non_stream(
    client: TestClient,
    *,
    input_text: str,
    project_id: str,
    session_id: str,
    model: str,
    max_output_tokens: int,
) -> None:
    response = client.post(
        "/openai/v1/responses",
        json={
            "model": model,
            "input": input_text,
            "stream": False,
            "project_id": project_id,
            "session_id": session_id,
            "max_output_tokens": max_output_tokens,
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"responses non-stream failed: {response.status_code} {response.text}")
    _ = response.json()


def _responses_stream(
    client: TestClient,
    *,
    input_text: str,
    project_id: str,
    session_id: str,
    model: str,
    max_output_tokens: int,
) -> None:
    with client.stream(
        "POST",
        "/openai/v1/responses",
        json={
            "model": model,
            "input": input_text,
            "stream": True,
            "project_id": project_id,
            "session_id": session_id,
            "max_output_tokens": max_output_tokens,
        },
    ) as response:
        if response.status_code != 200:
            raise RuntimeError(f"responses stream failed: {response.status_code} {response.text}")
        _consume_stream_lines(response)


def _embeddings(
    client: TestClient,
    *,
    model: str,
    embedding_inputs: list[str],
) -> None:
    response = client.post(
        "/openai/v1/embeddings",
        json={
            "model": model,
            "input": embedding_inputs,
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"embeddings failed: {response.status_code} {response.text}")
    _ = response.json()


def _models(client: TestClient) -> None:
    response = client.get("/openai/v1/models")
    if response.status_code != 200:
        raise RuntimeError(f"models failed: {response.status_code} {response.text}")
    _ = response.json()


def _run_mixed_worker(
    worker_id: int,
    cycles: int,
    long_prompt: str,
    embedding_inputs: list[str],
) -> MixedWorkerResult:
    chat_stream_ms: list[float] = []
    responses_stream_ms: list[float] = []
    chat_non_stream_ms: list[float] = []
    embeddings_ms: list[float] = []

    project_id = f"bench_mixed_proj_{worker_id}"
    session_id = f"bench_mixed_sess_{worker_id}"

    with TestClient(app) as client:
        for _ in range(max(1, cycles)):
            chat_stream_ms.append(
                _measure_one_call_ms(
                    lambda: _chat_stream(
                        client,
                        message_text=long_prompt,
                        project_id=project_id,
                        session_id=session_id,
                        model="bench-chat-stream-mixed",
                        max_tokens=512,
                    )
                )
            )
            responses_stream_ms.append(
                _measure_one_call_ms(
                    lambda: _responses_stream(
                        client,
                        input_text=long_prompt,
                        project_id=project_id,
                        session_id=session_id,
                        model="bench-responses-stream-mixed",
                        max_output_tokens=512,
                    )
                )
            )
            chat_non_stream_ms.append(
                _measure_one_call_ms(
                    lambda: _chat_non_stream(
                        client,
                        message_text=long_prompt,
                        project_id=project_id,
                        session_id=session_id,
                        model="bench-chat-non-stream-mixed",
                        max_tokens=512,
                    )
                )
            )
            embeddings_ms.append(
                _measure_one_call_ms(
                    lambda: _embeddings(
                        client,
                        model="bench-embed-mixed",
                        embedding_inputs=embedding_inputs,
                    )
                )
            )

    return MixedWorkerResult(
        chat_stream_ms=chat_stream_ms,
        responses_stream_ms=responses_stream_ms,
        chat_non_stream_ms=chat_non_stream_ms,
        embeddings_ms=embeddings_ms,
    )


def _run_mixed_load(
    *,
    workers: int,
    cycles: int,
    long_prompt: str,
    embedding_inputs: list[str],
) -> dict[str, object]:
    safe_workers = max(1, workers)
    safe_cycles = max(1, cycles)

    started_ns = time.perf_counter_ns()
    merged_chat_stream: list[float] = []
    merged_responses_stream: list[float] = []
    merged_chat_non_stream: list[float] = []
    merged_embeddings: list[float] = []

    with ThreadPoolExecutor(max_workers=safe_workers) as executor:
        futures = [
            executor.submit(
                _run_mixed_worker,
                worker_id,
                safe_cycles,
                long_prompt,
                embedding_inputs,
            )
            for worker_id in range(safe_workers)
        ]
        for future in as_completed(futures):
            worker_result = future.result()
            merged_chat_stream.extend(worker_result.chat_stream_ms)
            merged_responses_stream.extend(worker_result.responses_stream_ms)
            merged_chat_non_stream.extend(worker_result.chat_non_stream_ms)
            merged_embeddings.extend(worker_result.embeddings_ms)

    finished_ns = time.perf_counter_ns()
    wall_time_ms = (finished_ns - started_ns) / 1_000_000.0
    total_requests = len(merged_chat_stream) + len(merged_responses_stream) + len(merged_chat_non_stream) + len(merged_embeddings)
    throughput_rps = 0.0
    if wall_time_ms > 0:
        throughput_rps = total_requests / (wall_time_ms / 1000.0)

    return {
        "config": {
            "workers": safe_workers,
            "cycles_per_worker": safe_cycles,
            "long_prompt_chars": len(long_prompt),
            "embedding_batch_size": len(embedding_inputs),
            "embedding_text_chars": len(embedding_inputs[0]) if embedding_inputs else 0,
        },
        "totals": {
            "total_requests": total_requests,
            "wall_time_ms": _round3(wall_time_ms),
            "throughput_rps": _round3(throughput_rps),
        },
        "metrics": {
            "mixed_chat_stream": _summarize(merged_chat_stream).as_dict(),
            "mixed_responses_stream": _summarize(merged_responses_stream).as_dict(),
            "mixed_chat_non_stream_long": _summarize(merged_chat_non_stream).as_dict(),
            "mixed_embeddings_large_batch": _summarize(merged_embeddings).as_dict(),
        },
    }


def main() -> None:
    args = _parse_args()
    json_out: Path = args.json_out
    json_out.parent.mkdir(parents=True, exist_ok=True)

    memory_ledger.reset(clear_file=True)

    short_prompt = "summarize milestone status and pending risks"
    short_response_prompt = "provide status, todo, and risk summary"
    short_embeddings = [
        "context ledger benchmark sentence one",
        "context ledger benchmark sentence two",
        "context ledger benchmark sentence one",
    ]

    with TestClient(app) as client:
        for _ in range(max(1, args.warmup_runs)):
            _chat_non_stream(
                client,
                message_text=short_prompt,
                project_id="bench_compat",
                session_id="bench_compat_sess",
                model="bench-chat",
                max_tokens=256,
            )
            _responses_non_stream(
                client,
                input_text=short_response_prompt,
                project_id="bench_compat",
                session_id="bench_compat_sess",
                model="bench-responses",
                max_output_tokens=256,
            )
            _embeddings(client, model="bench-embed", embedding_inputs=short_embeddings)
            _models(client)

        chat_non_stream_ms = _measure_ms(
            lambda: _chat_non_stream(
                client,
                message_text=short_prompt,
                project_id="bench_compat",
                session_id="bench_compat_sess",
                model="bench-chat",
                max_tokens=256,
            ),
            args.chat_runs,
        )
        chat_stream_ms = _measure_ms(
            lambda: _chat_stream(
                client,
                message_text="stream milestone status with concise bullet points",
                project_id="bench_compat",
                session_id="bench_compat_sess",
                model="bench-chat-stream",
                max_tokens=256,
            ),
            args.chat_runs,
        )

        responses_non_stream_ms = _measure_ms(
            lambda: _responses_non_stream(
                client,
                input_text=short_response_prompt,
                project_id="bench_compat",
                session_id="bench_compat_sess",
                model="bench-responses",
                max_output_tokens=256,
            ),
            args.responses_runs,
        )
        responses_stream_ms = _measure_ms(
            lambda: _responses_stream(
                client,
                input_text="stream status, todo, and risk summary",
                project_id="bench_compat",
                session_id="bench_compat_sess",
                model="bench-responses-stream",
                max_output_tokens=256,
            ),
            args.responses_runs,
        )

        embeddings_ms = _measure_ms(
            lambda: _embeddings(client, model="bench-embed", embedding_inputs=short_embeddings),
            args.embeddings_runs,
        )
        models_ms = _measure_ms(lambda: _models(client), args.models_runs)

    report: dict[str, object] = {
        "timestamp_utc": _now_iso(),
        "runs": {
            "chat": max(1, args.chat_runs),
            "responses": max(1, args.responses_runs),
            "embeddings": max(1, args.embeddings_runs),
            "models": max(1, args.models_runs),
            "warmup": max(1, args.warmup_runs),
        },
        "metrics": {
            "chat_non_stream": _summarize(chat_non_stream_ms).as_dict(),
            "chat_stream": _summarize(chat_stream_ms).as_dict(),
            "responses_non_stream": _summarize(responses_non_stream_ms).as_dict(),
            "responses_stream": _summarize(responses_stream_ms).as_dict(),
            "embeddings": _summarize(embeddings_ms).as_dict(),
            "models": _summarize(models_ms).as_dict(),
        },
    }

    if not args.skip_mixed:
        long_prompt = _build_long_prompt(args.long_prompt_chars)
        large_embedding_inputs = _build_embedding_inputs(
            args.embedding_batch_size,
            args.embedding_text_chars,
        )
        report["mixed_load"] = _run_mixed_load(
            workers=args.mixed_workers,
            cycles=args.mixed_cycles,
            long_prompt=long_prompt,
            embedding_inputs=large_embedding_inputs,
        )

    if hasattr(memory_ledger, "sql_write_backpressure_stats"):
        report["sql_write_backpressure"] = memory_ledger.sql_write_backpressure_stats()

    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("OpenAI-compatible benchmark completed")
    print(f"report: {json_out.as_posix()}")
    for key, summary in report["metrics"].items():
        print(
            f"- {key}: mean={summary['mean_ms']}ms, "
            f"p50={summary['p50_ms']}ms, p95={summary['p95_ms']}ms, p99={summary['p99_ms']}ms"
        )

    mixed = report.get("mixed_load")
    if isinstance(mixed, dict):
        totals = mixed.get("totals", {})
        print(
            "- mixed totals: "
            f"requests={totals.get('total_requests')}, "
            f"wall={totals.get('wall_time_ms')}ms, "
            f"throughput={totals.get('throughput_rps')} rps"
        )
        mixed_metrics = mixed.get("metrics", {})
        if isinstance(mixed_metrics, dict):
            for key, summary in mixed_metrics.items():
                print(
                    f"  - {key}: mean={summary['mean_ms']}ms, "
                    f"p50={summary['p50_ms']}ms, p95={summary['p95_ms']}ms, p99={summary['p99_ms']}ms"
                )

    backpressure = report.get("sql_write_backpressure")
    if isinstance(backpressure, dict):
        print("- sql write backpressure stats:")
        for key in (
            "enabled",
            "pending_queue_size",
            "skipped_writes",
            "enqueued_writes",
            "dropped_writes",
            "replayed_writes",
            "replay_failed_writes",
            "direct_failed_writes",
        ):
            if key in backpressure:
                print(f"  - {key}: {backpressure[key]}")


if __name__ == "__main__":
    main()
