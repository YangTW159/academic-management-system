from campus_system.db import fetch_all, fetch_one


def build_shortcuts(role):
    if role == "admin":
        return ["维护学生档案", "发布校园通知", "调整宿舍分配", "查看系统日志"]
    if role == "teacher":
        return ["查看授课课程", "录入课程成绩", "追踪课程通知"]
    if role == "student":
        return ["查看个人课表", "查询成绩分析", "确认宿舍信息"]
    return ["维护宿舍信息", "查看床位情况", "发布宿舍通知"]


def get_student_profile(sno):
    return fetch_one(
        """
        SELECT
          s.sno, s.sname, s.sgender,
          DATE_FORMAT(s.sbirth, '%%Y-%%m-%%d') AS sbirth,
          s.sphone, s.class_id, s.dorm_id, s.status,
          c.class_name, c.major, c.college,
          CASE WHEN d.dorm_id IS NULL THEN '未分配'
               ELSE CONCAT(d.building, '-', d.room) END AS dorm_summary
        FROM student s
        LEFT JOIN class_info c ON s.class_id = c.class_id
        LEFT JOIN dormitory d ON s.dorm_id = d.dorm_id
        WHERE s.sno = %s
        """,
        (sno,),
    )


def get_course_profile(cno):
    return fetch_one(
        """
        SELECT
          c.cno, c.cname, c.cperiod, c.credit, c.tno,
          c.schedule_info, c.classroom, c.weeks, c.status,
          t.tname AS teacher_name,
          COUNT(sc.sno) AS selected_count
        FROM course c
        LEFT JOIN teacher t ON c.tno = t.tno
        LEFT JOIN sc ON c.cno = sc.cno
        WHERE c.cno = %s
        GROUP BY c.cno, c.cname, c.cperiod, c.credit, c.tno,
                 c.schedule_info, c.classroom, c.weeks, c.status, t.tname
        """,
        (cno,),
    )


def get_visible_notices(user, keyword=""):
    rows = fetch_all(
        """
        SELECT nid, title, content,
               DATE_FORMAT(publish_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS publish_time,
               publisher, publisher_role, scope, category, pinned, status
        FROM notice
        ORDER BY pinned DESC, publish_time DESC
        """
    )
    keyword = (keyword or "").strip()

    student_row = None
    class_name = ""
    if user["role"] == "student":
        student_row = fetch_one(
            "SELECT c.class_name FROM student s LEFT JOIN class_info c ON s.class_id = c.class_id WHERE s.sno = %s",
            (user["related_id"],),
        )
        class_name = student_row["class_name"] if student_row else ""

    buildings = []
    if user["role"] == "dormManager":
        building_rows = fetch_all(
            "SELECT building FROM dormitory WHERE dm_id = %s", (user["related_id"],)
        )
        buildings = [f"{row['building']}栋" for row in building_rows]

    visible_rows = []
    for row in rows:
        scope = row["scope"] or ""
        if user["role"] == "admin":
            allowed = True
        elif user["role"] == "student":
            allowed = scope in {"全校", "全员", "在读学生", class_name}
        elif user["role"] == "teacher":
            allowed = scope in {"全校", "全员", "教师"} or row["publisher_role"] == "teacher"
        elif user["role"] == "dormManager":
            allowed = scope in {"全校", "全员", "宿管"} or scope in buildings
        else:
            allowed = False

        if not allowed:
            continue
        if keyword and keyword not in row["title"] and keyword not in row["content"]:
            continue
        visible_rows.append(row)
    return visible_rows


def get_dashboard_payload(user):
    summary = fetch_one(
        """
        SELECT
          (SELECT COUNT(*) FROM student) AS total_students,
          (SELECT COUNT(*) FROM student WHERE status = '在读') AS active_students,
          (SELECT COUNT(*) FROM course) AS total_courses,
          (SELECT COUNT(*) FROM course WHERE status = '开课中') AS open_courses,
          (SELECT COUNT(*) FROM dormitory) AS total_dorms,
          (SELECT ROUND(IFNULL(SUM(cur_num) / NULLIF(SUM(max_num), 0) * 100, 0), 1)
           FROM dormitory) AS bed_usage_rate,
          (SELECT COUNT(*) FROM notice) AS total_notices
        """
    )

    class_distribution = fetch_all(
        """
        SELECT c.class_name AS label, COUNT(s.sno) AS value
        FROM class_info c LEFT JOIN student s ON c.class_id = s.class_id
        GROUP BY c.class_id, c.class_name ORDER BY c.class_id
        """
    )
    course_scores = fetch_all(
        """
        SELECT c.cname AS label, ROUND(IFNULL(AVG(sc.score), 0), 1) AS value
        FROM course c LEFT JOIN sc ON c.cno = sc.cno
        GROUP BY c.cno, c.cname ORDER BY c.cno
        """
    )
    notice_stats = fetch_all(
        """
        SELECT category AS label, COUNT(*) AS value FROM notice
        GROUP BY category ORDER BY COUNT(*) DESC, category
        """
    )

    latest_notices = get_visible_notices(user)[:5]
    recent_logs = fetch_all(
        """
        SELECT log_id, actor, action_name, target_name,
               DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
        FROM operation_log ORDER BY log_id DESC LIMIT 8
        """
    ) if user["role"] == "admin" else fetch_all(
        """
        SELECT log_id, actor, action_name, target_name,
               DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at
        FROM operation_log WHERE actor = %s
        ORDER BY log_id DESC LIMIT 8
        """,
        (user["display_name"],),
    )

    return {
        "summary": summary,
        "charts": {
            "class_distribution": class_distribution,
            "course_scores": course_scores,
            "notice_stats": notice_stats,
        },
        "latest_notices": latest_notices,
        "recent_logs": recent_logs,
        "shortcuts": build_shortcuts(user["role"]),
    }
