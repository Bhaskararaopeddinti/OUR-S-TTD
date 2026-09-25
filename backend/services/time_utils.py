"""
OURS TTD – Time & Timezone Utilities
Provides standard India Standard Time (IST) handling (UTC+05:30)
and formatted date/time representations for admin updates and pilgrim dashboards.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

# Indian Standard Time (UTC+05:30)
IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TZ = timezone(IST_OFFSET, name="IST")

def get_now_ist() -> datetime:
    """Return the current datetime localized in India Standard Time (IST)."""
    return datetime.now(IST_TZ)

def to_ist(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert a datetime (naive UTC or aware) to India Standard Time (IST)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume naive datetime is stored in UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST_TZ)

def calculate_tithi(date_obj: datetime) -> str:
    """Calculate Hindu lunar tithi approximation for a given date."""
    try:
        epoch = datetime(2000, 1, 6, tzinfo=timezone.utc)
        target = date_obj if date_obj.tzinfo else date_obj.replace(tzinfo=timezone.utc)
        diff_days = (target - epoch).total_seconds() / 86400.0
        lunar_month = 29.53058867
        tithi_num = int((diff_days % lunar_month) / lunar_month * 30) + 1
        tithi_names = [
            "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
            "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
            "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
            "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
        ]
        if 1 <= tithi_num <= len(tithi_names):
            return tithi_names[tithi_num - 1]
    except Exception:
        pass
    return "Shukla Paksha"

def format_admin_timestamp(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Format a datetime for admin data storage and dashboard presentation in IST.
    Example output:
      upload_date: "25 Sep 2026"
      upload_time: "8:40 PM IST"
      formatted_ist: "25 Sep 2026, 8:40 PM IST"
      day_of_week: "Friday"
      tithi: "Ekadashi"
    """
    dt_ist = to_ist(dt) if dt is not None else get_now_ist()
    upload_date = dt_ist.strftime("%d %b %Y")
    upload_time = dt_ist.strftime("%I:%M %p IST").lstrip("0")
    formatted_ist = f"{upload_date}, {upload_time}"
    day_of_week = dt_ist.strftime("%A")
    tithi = calculate_tithi(dt_ist)

    return {
        "upload_date": upload_date,
        "upload_time": upload_time,
        "formatted_ist": formatted_ist,
        "day_of_week": day_of_week,
        "tithi": tithi,
        "iso_utc": (dt if (dt and dt.tzinfo) else dt_ist.astimezone(timezone.utc)).isoformat() if dt else datetime.now(timezone.utc).isoformat(),
        "iso_ist": dt_ist.isoformat()
    }


def get_latest_admin_update_info(db) -> Dict[str, Any]:
    """
    Retrieve the latest authorized admin update across AdminUpdateMeta,
    CrowdAnalysis, PilgrimFlowData, and CCTVCrowdRecord.
    Returns structured timestamp info formatted for India Standard Time (IST).
    """
    if db is None:
        return {
            "has_admin_data": False,
            "upload_date": None,
            "upload_time": None,
            "data_timestamp": None,
            "admin_update_timestamp": None,
            "formatted_ist": None,
            "display_text": "No latest update available",
            "day_of_week": None,
            "tithi": None,
            "summary": "No admin updates recorded yet."
        }

    from backend.models import AdminUpdateMeta, CrowdAnalysis, PilgrimFlowData, CCTVCrowdRecord
    from sqlalchemy import desc

    # 1. Check AdminUpdateMeta first
    latest_meta = db.query(AdminUpdateMeta).order_by(desc(AdminUpdateMeta.created_at)).first()
    if latest_meta:
        ts = latest_meta.admin_update_timestamp or latest_meta.created_at
        formatted = format_admin_timestamp(ts)
        return {
            "has_admin_data": True,
            "upload_date": latest_meta.upload_date or formatted["upload_date"],
            "upload_time": latest_meta.upload_time or formatted["upload_time"],
            "data_timestamp": (latest_meta.data_timestamp or ts).isoformat(),
            "admin_update_timestamp": ts.isoformat(),
            "formatted_ist": latest_meta.formatted_ist or formatted["formatted_ist"],
            "display_text": latest_meta.formatted_ist or formatted["formatted_ist"],
            "day_of_week": formatted["day_of_week"],
            "tithi": formatted["tithi"],
            "summary": latest_meta.summary or latest_meta.update_type
        }

    # 2. Check CrowdAnalysis
    latest_ca = db.query(CrowdAnalysis).order_by(desc(CrowdAnalysis.created_at)).first()
    if latest_ca:
        ts = latest_ca.created_at
        formatted = format_admin_timestamp(ts)
        return {
            "has_admin_data": True,
            "upload_date": latest_ca.upload_date or formatted["upload_date"],
            "upload_time": latest_ca.upload_time or formatted["upload_time"],
            "data_timestamp": ts.isoformat(),
            "admin_update_timestamp": ts.isoformat(),
            "formatted_ist": formatted["formatted_ist"],
            "display_text": formatted["formatted_ist"],
            "day_of_week": formatted["day_of_week"],
            "tithi": formatted["tithi"],
            "summary": f"Admin crowd photo analysis ({latest_ca.crowd_level})"
        }

    # 3. Check CCTVCrowdRecord (real camera / uploaded media)
    latest_cctv = db.query(CCTVCrowdRecord).filter(
        CCTVCrowdRecord.source.in_(["cctv_image", "admin_image", "cctv_ai", "authorized_cctv"])
    ).order_by(desc(CCTVCrowdRecord.timestamp)).first()
    if latest_cctv:
        ts = latest_cctv.timestamp or latest_cctv.created_at
        formatted = format_admin_timestamp(ts)
        return {
            "has_admin_data": True,
            "upload_date": formatted["upload_date"],
            "upload_time": formatted["upload_time"],
            "data_timestamp": ts.isoformat(),
            "admin_update_timestamp": ts.isoformat(),
            "formatted_ist": formatted["formatted_ist"],
            "display_text": formatted["formatted_ist"],
            "day_of_week": formatted["day_of_week"],
            "tithi": formatted["tithi"],
            "summary": f"CCTV crowd analysis: {latest_cctv.queue_status}"
        }

    # 4. Check PilgrimFlowData with valid admin entry
    latest_flow = db.query(PilgrimFlowData).filter(
        PilgrimFlowData.source.in_(["admin_image", "cctv_ai", "manual", "authorized_cctv"])
    ).order_by(desc(PilgrimFlowData.created_at)).first()
    if latest_flow and latest_flow.created_at:
        ts = latest_flow.created_at
        formatted = format_admin_timestamp(ts)
        return {
            "has_admin_data": True,
            "upload_date": formatted["upload_date"],
            "upload_time": formatted["upload_time"],
            "data_timestamp": ts.isoformat(),
            "admin_update_timestamp": ts.isoformat(),
            "formatted_ist": formatted["formatted_ist"],
            "display_text": formatted["formatted_ist"],
            "day_of_week": formatted["day_of_week"],
            "tithi": formatted["tithi"],
            "summary": f"Pilgrim flow slot {latest_flow.start_time}-{latest_flow.end_time}"
        }

    # 5. No admin data yet
    return {
        "has_admin_data": False,
        "upload_date": None,
        "upload_time": None,
        "data_timestamp": None,
        "admin_update_timestamp": None,
        "formatted_ist": None,
        "display_text": "No latest update available",
        "day_of_week": None,
        "tithi": None,
        "summary": "No admin updates recorded yet."
    }


def record_admin_update(
    db,
    update_type: str,
    summary: str = "",
    admin_id: Optional[int] = None,
    data_timestamp: Optional[datetime] = None
):
    """Helper to record an authorized admin update with exact IST formatting."""
    from backend.models import AdminUpdateMeta
    now_utc = datetime.utcnow()
    fmt = format_admin_timestamp(now_utc)
    meta = AdminUpdateMeta(
        update_type=update_type,
        upload_date=fmt["upload_date"],
        upload_time=fmt["upload_time"],
        data_timestamp=data_timestamp or now_utc,
        admin_update_timestamp=now_utc,
        formatted_ist=fmt["formatted_ist"],
        summary=summary,
        admin_id=admin_id,
        created_at=now_utc
    )
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta
