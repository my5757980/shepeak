"""Identity binding helper for the security suite."""


def set_identity(conn, role: str, athlete_id: str = "", coach_id: str = "") -> None:
    conn.execute("SELECT set_config('app.role', %s, false)", (role,))
    conn.execute("SELECT set_config('app.athlete_id', %s, false)", (athlete_id,))
    conn.execute("SELECT set_config('app.coach_id', %s, false)", (coach_id,))
