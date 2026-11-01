#!/usr/bin/env python3
"""
Email Sender

smtplib를 사용하여 이메일을 발송하는 도구.
환경 변수로 SMTP 설정을 받음.

앱 비밀번호 생성 방법 (Gmail 기준): 
- https://myaccount.google.com/security 접속 → 2단계 인증 활성화 (이미 돼 있으면 skip)
- https://myaccount.google.com/apppasswords 접속
- 앱 이름 입력 (예: OSS SMTP) → 만들기 클릭
- 생성된 16자리 코드 (공백 제거)를 SMTP_PASSWORD로 사용
"""

import sys
import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional
from pathlib import Path
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(path: Path) -> None:
        """Load simple KEY=VALUE pairs, including quoted multiline values."""
        pending_key = None
        pending_lines: list[str] = []

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if pending_key:
                if line.endswith('"'):
                    pending_lines.append(line[:-1])
                    os.environ.setdefault(pending_key, "\n".join(pending_lines))
                    pending_key = None
                    pending_lines = []
                else:
                    pending_lines.append(raw_line)
                continue

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and not (len(value) > 1 and value.endswith('"')):
                pending_key = key
                pending_lines = [value[1:]]
            else:
                os.environ.setdefault(key, value.strip('"'))

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)


def recipients_env(subject: Optional[str] = None) -> str:
    """주제별 수신자 환경 변수 이름. ai -> RECIPIENTS_AI, semi-conductor -> RECIPIENTS_SEMI_CONDUCTOR."""
    if not subject:
        return "RECIPIENTS"
    return "RECIPIENTS_" + re.sub(r"[^0-9A-Za-z]+", "_", subject).upper()


def get_recipients(subject: Optional[str] = None) -> list[str]:
    """수신자 목록을 파싱하여 반환.

    주제가 주어지면 주제별 변수(RECIPIENTS_<주제>)를 먼저 보고, 비어 있으면 RECIPIENTS 를 씀.
    쉼표(,) 또는 줄바꿈(\\n) 구분자를 모두 지원:
      RECIPIENTS=a@b.com,c@d.com
      RECIPIENTS_AI="a@b.com
      c@d.com"
    """
    raw = os.getenv(recipients_env(subject), "") or os.getenv("RECIPIENTS", "")
    recipients = [r.strip() for r in re.split(r"[,\n]", raw) if r.strip()]
    return recipients


def send_email(
    to: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
    sender_name: Optional[str] = None
) -> bool:
    """
    이메일 발송

    Args:
        to: 수신자 이메일
        subject: 제목
        body_text: 본문 (텍스트)
        body_html: 본문 (HTML, 선택)
        smtp_server: SMTP 서버 (환경 변수 SMTP_SERVER 또는 인자)
        smtp_port: SMTP 포트 (환경 변수 SMTP_PORT 또는 인자, 기본: 587)
        smtp_user: SMTP 사용자 (환경 변수 SMTP_USER 또는 인자)
        smtp_password: SMTP 비밀번호 (환경 변수 SMTP_PASSWORD 또는 인자)
        sender_name: 보낸사람 표시 이름 (선택, 예: "AI 뉴스레터")

    Returns:
        성공 여부
    """
    smtp_server = smtp_server or os.getenv("SMTP_SERVER")
    smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
    smtp_user = smtp_user or os.getenv("SMTP_USER")
    smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")

    if not all([smtp_server, smtp_user, smtp_password]):
        print("Error: SMTP configuration missing. Set SMTP_SERVER, SMTP_USER, SMTP_PASSWORD environment variables.", file=sys.stderr)
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((sender_name, smtp_user)) if sender_name else smtp_user
        msg['To'] = to

        part1 = MIMEText(body_text, 'plain')
        msg.attach(part1)

        if body_html:
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to, msg.as_string())

        print(f"Email sent successfully to {to}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}", file=sys.stderr)
        return False


def main():
    """CLI 진입점

    ============================================================
    [Gmail 사전 설정 가이드]
    ============================================================

    1. Google 계정 2단계 인증 활성화
       - https://myaccount.google.com/security 접속
       - '2단계 인증' 클릭 → 활성화

    2. Gmail 앱 비밀번호 생성
       - https://myaccount.google.com/apppasswords 접속
       - '앱 선택' → '메일', '기기 선택' → '기타(직접 입력)' → 이름 입력
       - 생성된 16자리 앱 비밀번호 복사 (공백 제거 후 사용)

    3. Gmail SMTP 설정 확인
       - Gmail → 설정(톱니바퀴) → '모든 설정 보기'
       - '전달 및 POP/IMAP' 탭 → IMAP 사용 → '변경사항 저장'

    4. .env 파일 생성 (이 파일과 같은 디렉토리)
       --------------------------------------------------
       SMTP_SERVER=smtp.gmail.com
       SMTP_PORT=587
       SMTP_USER=your-email@gmail.com
       SMTP_PASSWORD=abcd efgh ijkl mnop   # 앱 비밀번호 (공백 포함 가능)
       --------------------------------------------------

    5. .env에 수신자 설정
       RECIPIENTS=user1@example.com,user2@example.com
       RECIPIENTS_AI=user3@example.com        # 선택. 주제별 수신자 (없으면 RECIPIENTS 사용)

    6. 의존 패키지 설치
       pip install -r requirements.txt

    7. 실행 예시
       python email_sender.py "제목" "본문 텍스트"
    ============================================================
    """
    if len(sys.argv) < 3:
        print("Usage: email_sender.py <subject> <body_text> [<body_html>]")
        print("Environment variables: SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, RECIPIENTS")
        sys.exit(1)

    subject = sys.argv[1]
    body_text = sys.argv[2]
    body_html = sys.argv[3] if len(sys.argv) > 3 else None

    recipients = get_recipients()
    if not recipients:
        print("Error: RECIPIENTS environment variable is not set or empty.", file=sys.stderr)
        sys.exit(1)

    print(f"Sending to {len(recipients)} recipient(s): {', '.join(recipients)}")
    all_success = True
    for to in recipients:
        if not send_email(to, subject, body_text, body_html):
            all_success = False

    if not all_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
