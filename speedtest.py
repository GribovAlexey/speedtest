from __future__ import annotations

import argparse
import os
import sys
import time

import requests
from dotenv import load_dotenv

DEFAULT_URL = "https://upload.wikimedia.org/wikipedia/commons/3/3d/LARGE_elevation.jpg"
MB = 1024 * 1024


def fetch(url: str, timeout: float, session: requests.Session) -> tuple[float, int]:
    """
    :param url:
    :param timeout:
    :param session:
    :return:
    """
    start = time.perf_counter()
    resp = session.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "speedtest/1.0",
            "Cache-Control": "no-cache",
        },
    )
    resp.raise_for_status()
    size = len(resp.content)
    elapsed = time.perf_counter() - start
    return elapsed, size


def run(url: str, count: int, timeout: float) -> int:
    """
    :param url:
    :param count:
    :param timeout:
    :return:
    """
    print(f"URL:      {url}")
    print(f"Запросов: {count}")
    print(f"Таймаут:  {timeout} с\n")

    times: list[float] = []
    total_bytes = 0
    errors = 0

    with requests.Session() as session:
        for i in range(1, count + 1):
            try:
                elapsed, size = fetch(url, timeout, session)
            except requests.RequestException as exc:
                errors += 1
                print(f"[{i:2}/{count}] ошибка: {exc}")
                continue

            times.append(elapsed)
            total_bytes += size
            mb = size / MB
            speed = mb / elapsed if elapsed > 0 else 0.0
            print(f"[{i:2}/{count}] {elapsed:6.3f} с  {mb:6.2f} МБ  →  {speed:6.2f} МБ/с")

    if not times:
        print("\nНи одного успешного запроса.")
        return 1

    total_time = sum(times)
    total_mb = total_bytes / MB
    avg_time = total_time / len(times)
    avg_speed = total_mb / total_time if total_time > 0 else 0.0

    print("\n=== Итог ===")
    print(f"Успешных:          {len(times)} из {count}" + (f" (ошибок: {errors})" if errors else ""))
    print(f"Скачано:           {total_mb:.2f} МБ")
    print(f"Общее время:       {total_time:.2f} с")
    print(f"Среднее время:     {avg_time:.2f} с")
    print(f"Средняя скорость:  {avg_speed:.2f} МБ/с")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="speedtest",
        description="Последовательный замер скорости скачивания.",
    )
    parser.add_argument("url", nargs="?", help="URL ресурса (перебивает SPEEDTEST_URL)")
    parser.add_argument("-n", "--requests", type=int, help="Сколько запросов сделать")
    parser.add_argument("-t", "--timeout", type=float, help="Таймаут одного запроса, сек")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)

    url = args.url or os.getenv("SPEEDTEST_URL", DEFAULT_URL)
    count = args.requests or int(os.getenv("SPEEDTEST_REQUESTS", "10"))
    timeout = args.timeout or float(os.getenv("SPEEDTEST_TIMEOUT", "30"))

    if count <= 0:
        print("Количество запросов должно быть > 0", file=sys.stderr)
        return 2

    return run(url, count, timeout)


if __name__ == "__main__":
    sys.exit(main())