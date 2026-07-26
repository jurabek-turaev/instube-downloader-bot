import os
import tempfile

from openpyxl import Workbook
from openpyxl.styles import Font

from config import DOWNLOADS_DIR
from services.database import get_all_users

HEADERS = [
    "Telegram ID", "Username", "Full name", "Language",
    "Joined at", "Last active", "Downloads", "Active",
]


def build_users_xlsx() -> str:
    """Write all users to an .xlsx file and return its path."""
    users = get_all_users()

    wb = Workbook()
    ws = wb.active
    ws.title = "Users"

    ws.append(HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)


    for u in users:
        ws.append([
            u["telegram_id"], u["username"], u["full_name"], u["language"],
            u["joined_at"], u["last_active"], u["downloads_count"], u["is_active"],
        ])

    for i, header in enumerate(HEADERS, start=1):
        ws.column_dimensions[chr(64 + i)].width = max(len(header) + 2, 16)

    fd, path = tempfile.mkstemp(suffix=".xlsx", dir=DOWNLOADS_DIR)
    os.close(fd)
    wb.save(path)
    return path
