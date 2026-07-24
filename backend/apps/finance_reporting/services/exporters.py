from io import BytesIO, StringIO
import csv

from openpyxl import Workbook

from common.csv_safe import csv_safe_value, spreadsheet_safe_value


def settlement_report_to_csv(report):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "trainer_id",
        "gross_amount",
        "refund_amount",
        "commission_amount",
        "payout_amount",
        "paid_amount",
        "pending_amount",
        "order_count",
        "refund_count",
        "payout_count",
        "last_order_at",
    ])
    for line in report.lines.select_related("trainer").all():
        writer.writerow([csv_safe_value(value) for value in [
            line.trainer_id,
            line.gross_amount,
            line.refund_amount,
            line.commission_amount,
            line.payout_amount,
            line.paid_amount,
            line.pending_amount,
            line.order_count,
            line.refund_count,
            line.payout_count,
            line.last_order_at.isoformat() if line.last_order_at else "",
        ]])
    return output.getvalue().encode("utf-8")


def settlement_report_to_xlsx(report):
    wb = Workbook()
    ws = wb.active
    ws.title = "settlement"
    ws.append([
        "trainer_id",
        "gross_amount",
        "refund_amount",
        "commission_amount",
        "payout_amount",
        "paid_amount",
        "pending_amount",
        "order_count",
        "refund_count",
        "payout_count",
        "last_order_at",
    ])
    for line in report.lines.select_related("trainer").all():
        ws.append([spreadsheet_safe_value(value) for value in [
            str(line.trainer_id),
            float(line.gross_amount),
            float(line.refund_amount),
            float(line.commission_amount),
            float(line.payout_amount),
            float(line.paid_amount),
            float(line.pending_amount),
            line.order_count,
            line.refund_count,
            line.payout_count,
            line.last_order_at.isoformat() if line.last_order_at else "",
        ]])
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()
