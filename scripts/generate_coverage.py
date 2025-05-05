#!/usr/bin/env python3
"""
테스트 커버리지 보고서 생성 스크립트

이 스크립트는 pytest-cov를 사용하여 테스트 커버리지를 측정하고,
다양한 형식(HTML, XML, JSON)의 보고서를 생성합니다.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_ROOT / "coverage"


def setup_directories():
    """필요한 디렉토리 생성"""
    COVERAGE_DIR.mkdir(exist_ok=True)
    (COVERAGE_DIR / "html").mkdir(exist_ok=True)


def run_tests_with_coverage(args):
    """지정된 옵션으로 테스트 및 커버리지 측정 실행"""
    cmd = [
        "pytest",
        f"--cov={','.join(args.source)}",
        "--cov-config=.coveragerc",
    ]

    # 마커 추가 (있는 경우)
    if args.markers:
        cmd.append(f"-m {args.markers}")

    # 테스트 경로 추가 (지정된 경우)
    if args.testpaths:
        cmd.extend(args.testpaths)

    # 보고서 형식 추가 - 각 형식을 개별 옵션으로 추가
    if args.html:
        cmd.append("--cov-report=html")
    if args.xml:
        cmd.append("--cov-report=xml")
    if args.json:
        cmd.append("--cov-report=json")
    if args.term:
        cmd.append("--cov-report=term-missing:skip-covered")

    # 추가 pytest 인자 추가
    if args.pytest_args:
        cmd.extend(args.pytest_args)

    # 명령어 실행
    print(f"실행 명령어: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def show_summary(args):
    """커버리지 보고서 생성 요약 표시"""
    print("\n=== 커버리지 보고서 생성 완료 ===")

    if args.html:
        html_path = COVERAGE_DIR / "html" / "index.html"
        if html_path.exists():
            print(f"HTML 보고서: {html_path}")

    if args.xml:
        xml_path = COVERAGE_DIR / "coverage.xml"
        if xml_path.exists():
            print(f"XML 보고서: {xml_path}")

    if args.json:
        json_path = COVERAGE_DIR / "coverage.json"
        if json_path.exists():
            print(f"JSON 보고서: {json_path}")


def parse_args():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(description="테스트 실행 및 커버리지 보고서 생성")

    # 소스 패키지 설정
    parser.add_argument(
        "--source",
        nargs="+",
        default=["app", "common", "pipelines"],
        help="커버리지를 측정할 소스 패키지 (기본값: app common pipelines)",
    )

    # 테스트 경로 설정
    parser.add_argument(
        "testpaths",
        nargs="*",
        help="실행할 테스트 경로 (기본값: pytest.ini의 testpaths 사용)",
    )

    # 마커 설정
    parser.add_argument(
        "-m",
        "--markers",
        help="실행할 테스트의 마커 표현식 (예: 'unit and not slow')",
    )

    # 보고서 형식 설정
    parser.add_argument(
        "--html",
        action="store_true",
        default=True,
        help="HTML 보고서 생성 (기본값: True)",
    )
    parser.add_argument(
        "--xml",
        action="store_true",
        default=True,
        help="XML 보고서 생성 (기본값: True)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=True,
        help="JSON 보고서 생성 (기본값: True)",
    )
    parser.add_argument(
        "--term",
        action="store_true",
        default=True,
        help="터미널 보고서 생성 (기본값: True)",
    )

    # 추가 pytest 인자
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        help="추가 pytest 인자 (-- 다음에 지정)",
    )

    return parser.parse_args()


def main():
    """메인 함수"""
    args = parse_args()
    setup_directories()

    try:
        exit_code = run_tests_with_coverage(args)
        show_summary(args)
        return exit_code
    except Exception as e:
        print(f"오류 발생: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
