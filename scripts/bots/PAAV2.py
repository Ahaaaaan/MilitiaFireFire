def run(state, memory):
    did_attack = False

    if not memory:
        memory = {
            "roam_dir":          1,
            "roam_ticks":        240,
            "evade_dir":         1,
            "evade_ticks":       0,
            "strafe_dir":        1,
            "strafe_ticks":      0,
            "grenade_tick":      0,
            "dodge_tick":        0,
            "target_id":         -1,
            "target_health":     -1.0,
            "no_damage_ticks":   0,
            "target_x":          0.0,
            "target_y":          0.0,
            "stable_ticks":      0,
            "last_x":            0.0,
            "last_y":            0.0,
            "stuck_ticks":       0,
            "nade_escape_ticks": 0,
            "nade_escape_dir":   1,
            "fly_tick":          0,
            "flee_ticks":        0,
            "flee_dir":          1,
            "hunt_id":           -1,   # global marker target we are hunting
        }

    enemies     = state.enemy_positions()
    markers     = state.player_markers()
    ammo_cur, ammo_reserve = state.my_ammo()
    grenades    = state.my_grenades()
    health      = state.my_health()
    fuel        = state.my_fuel()
    current_aim = state.my_aim_angle()
    my_x, my_y  = state.my_position()
    my_gun_id   = state.my_gun()

    memory.setdefault("target_id",          -1)
    memory.setdefault("target_health",      -1.0)
    memory.setdefault("no_damage_ticks",     0)
    memory.setdefault("target_x",           0.0)
    memory.setdefault("target_y",           0.0)
    memory.setdefault("stable_ticks",        0)
    memory.setdefault("grenade_tick",        0)
    memory.setdefault("dodge_tick",          0)
    memory.setdefault("last_x",             my_x)
    memory.setdefault("last_y",             my_y)
    memory.setdefault("stuck_ticks",         0)
    memory.setdefault("nade_escape_ticks",   0)
    memory.setdefault("nade_escape_dir",     1)
    memory.setdefault("fly_tick",            0)
    memory.setdefault("flee_ticks",          0)
    memory.setdefault("flee_dir",            1)
    memory.setdefault("hunt_id",            -1)

    # -----------------------------------------------------------------------
    # Constants
    # -----------------------------------------------------------------------
    GRENADE_ESCAPE_DIST    = 180.0
    STABLE_POS_TOLERANCE   = 10.0
    STABLE_TICKS_TO_THROW  = 4      # throw grenades sooner (was 6)
    GRENADE_COOLDOWN_TICKS = 50
    FLY_COOLDOWN_TICKS     = 2
    AIM_THRESHOLD          = 0.13

    # Aggression: close to melee range — no backing off unless escaping grenade
    HUNT_CLOSE_DIST        = 60.0   # try to get THIS close to weaker enemies
    MAX_FIGHT_DIST         = 280.0  # close gap if farther than this
    PRESSURE_DIST          = 120.0  # keep pressure inside this range

    # Flee only from enemies who massively outclass us
    FLEE_THREAT_THRESHOLD  = 50.0   # raised so we fight more (was 35)
    FLEE_DURATION_TICKS    = 60     # shorter flee (was 90)
    FLEE_SAFE_DIST         = 400.0

    UPGRADE_MARGIN         = 15

    weapon_scores = {
        0: 70, 1: 25, 2: 40, 3: 80, 4: 75, 5: 95,
        6: 35, 7: 60, 8: 50, 9: 55, 10: 65, 11: 90,
        12: 45, 13: 42, 14: 68, 15: 85,
    }

    my_score = weapon_scores.get(int(my_gun_id), 0) if my_gun_id is not None else 0

    # -----------------------------------------------------------------------
    # Cooldowns
    # -----------------------------------------------------------------------
    if memory["grenade_tick"]  > 0: memory["grenade_tick"]  -= 1
    if memory["dodge_tick"]    > 0: memory["dodge_tick"]    -= 1
    if memory["fly_tick"]      > 0: memory["fly_tick"]      -= 1
    if memory["flee_ticks"]    > 0: memory["flee_ticks"]    -= 1

    # -----------------------------------------------------------------------
    # Grenade escape (always highest priority)
    # -----------------------------------------------------------------------
    nades             = state.active_grenades()
    nearest_nade_dist = 1e9
    nearest_nade      = None
    for g in nades:
        nx, ny = float(g["x"]), float(g["y"])
        d = math.sqrt((nx - my_x)**2 + (ny - my_y)**2)
        if d < nearest_nade_dist:
            nearest_nade_dist = d
            nearest_nade      = g

    if nearest_nade is not None and nearest_nade_dist < GRENADE_ESCAPE_DIST:
        memory["nade_escape_dir"]   = -1 if my_x < float(nearest_nade["x"]) else 1
        memory["nade_escape_ticks"] = 18
    elif memory["nade_escape_ticks"] > 0:
        memory["nade_escape_ticks"] -= 1

    escaping_nade = memory["nade_escape_ticks"] > 0

    # -----------------------------------------------------------------------
    # SAW bullet evasion
    # -----------------------------------------------------------------------
    saw_bullets  = state.saw_bullets_in_view()
    incoming_saw = False
    for sb in saw_bullets:
        bx, by   = float(sb["x"]), float(sb["y"])
        bvx, bvy = float(sb["vx"]), float(sb["vy"])
        dot = bvx * (my_x - bx) + bvy * (my_y - by)
        if dot > 0 and float(sb["distance"]) < 300.0:
            incoming_saw = True
            break

    if incoming_saw and not escaping_nade and memory["dodge_tick"] <= 0:
        if memory["evade_dir"] == 1:
            move_right()
        else:
            move_left()
        jetpack()
        memory["dodge_tick"] = 20

    # -----------------------------------------------------------------------
    # Medkit seeking — only when very critically low
    # -----------------------------------------------------------------------
    seeking_medkit = False
    if health < 35.0:
        medkits = state.medkit_spawns()
        if medkits:
            mk = min(medkits, key=lambda m: math.sqrt((float(m["x"]) - my_x)**2 + (float(m["y"]) - my_y)**2))
            mk_dx   = float(mk["x"]) - my_x
            mk_dy   = float(mk["y"]) - my_y
            mk_dist = math.sqrt(mk_dx**2 + mk_dy**2)
            if mk_dist > 20.0:
                if mk_dx < 0:
                    move_left()
                else:
                    move_right()
                if mk_dy < -20.0 and fuel > 10.0:
                    jetpack()
                seeking_medkit = True

    # -----------------------------------------------------------------------
    # Opportunistic weapon upgrade (only if standing on it basically)
    # -----------------------------------------------------------------------
    for gs in state.gun_spawns():
        gs_id    = gs["weapon_id"]
        gs_score = weapon_scores.get(int(gs_id), 30) if gs_id is not None else 0
        gs_dist  = math.sqrt((float(gs["x"]) - my_x)**2 + (float(gs["y"]) - my_y)**2)
        if gs_score > my_score + UPGRADE_MARGIN and gs_dist < 40.0:
            pickup_gun(state)
            my_gun_id = state.my_gun()
            my_score  = weapon_scores.get(int(my_gun_id), 0) if my_gun_id is not None else 0
            break

    # -----------------------------------------------------------------------
    # Classify all visible enemies: weaker (hunt) vs stronger (flee/fight)
    # -----------------------------------------------------------------------
    weaker_enemies   = []
    stronger_enemies = []
    for e in enemies:
        e_gun_score = weapon_scores.get(int(e.get("current_gun", 1)), 25)
        hp_delta    = float(e["health"]) - health
        gun_delta   = e_gun_score - my_score
        threat      = hp_delta * 0.5 + gun_delta * 1.5
        if threat >= FLEE_THREAT_THRESHOLD:
            stronger_enemies.append(e)
        else:
            weaker_enemies.append(e)

    # Also classify marker targets by their stored threat info.
    # Markers don't expose health/gun so we use hunt_id memory to stick to
    # a previously identified weak target, or default to pursuing all markers.
    weaker_markers   = []
    stronger_markers = []
    for m in markers:
        # If we previously identified this marker as weak, keep hunting it.
        # Otherwise treat unknown markers as targets worth chasing.
        weaker_markers.append(m)

    # -----------------------------------------------------------------------
    # Resolve primary target
    # Hunting priority: closest weak enemy in sensor > closest weak marker
    #                   > closest strong enemy (fight or flee) > any marker
    # -----------------------------------------------------------------------
    hunt_target    = None   # a visible weak enemy dict
    flee_target    = None   # a visible strong enemy to flee from
    fight_target   = None   # fallback: fight whoever is closest
    marker_target  = None   # global marker to path toward

    if weaker_enemies:
        hunt_target  = min(weaker_enemies,  key=lambda e: e["distance"])
    if stronger_enemies:
        flee_target  = min(stronger_enemies, key=lambda e: e["distance"])
    if enemies:
        fight_target = min(enemies,          key=lambda e: e["distance"])
    if markers:
        marker_target = min(markers,         key=lambda m: m["distance"])

    # -----------------------------------------------------------------------
    # COMBAT BRANCH — at least one enemy in sensor radius
    # -----------------------------------------------------------------------
    if enemies:
        # Choose who to engage this frame.
        if hunt_target is not None:
            # We have a weaker prey — charge it down.
            target = hunt_target
            fleeing = False
        elif flee_target is not None and not weaker_enemies:
            # Only stronger enemies visible — flee if threshold met.
            target  = flee_target
            threat_val = (float(flee_target["health"]) - health) * 0.5 + \
                         (weapon_scores.get(int(flee_target.get("current_gun", 1)), 25) - my_score) * 1.5
            is_superior = threat_val >= FLEE_THREAT_THRESHOLD
            if is_superior and memory["flee_ticks"] <= 0:
                memory["flee_ticks"] = FLEE_DURATION_TICKS
                memory["flee_dir"]   = -1 if float(flee_target["x"]) > my_x else 1
            if memory["flee_ticks"] > 0 and (float(flee_target["distance"]) >= FLEE_SAFE_DIST or not is_superior):
                memory["flee_ticks"] = 0
            fleeing = memory["flee_ticks"] > 0
        else:
            target  = fight_target
            fleeing = False

        target_id     = int(target["id"])
        ex            = float(target["x"])
        ey            = float(target["y"])
        target_health = float(target["health"])
        distance      = float(target["distance"])
        dx            = ex - my_x
        dy            = ey - my_y
        angle         = math.atan2(dy, dx)

        # Line-of-sight
        obstacle_dist = state.distance_to_obstacle(angle, max_distance=2000.0, step=4.0)
        blocked       = obstacle_dist < max(0.0, distance - 20.0)

        # Aim always
        aim_error = angle - current_aim
        if aim_error >  math.pi: aim_error -= 2.0 * math.pi
        if aim_error < -math.pi: aim_error += 2.0 * math.pi

        if aim_error > 0.01:
            aim_right()
        elif aim_error < -0.01:
            aim_left()

        # Stability tracking for grenades
        if memory["target_id"] == target_id:
            t_moved = math.sqrt((ex - memory["target_x"])**2 + (ey - memory["target_y"])**2)
            memory["stable_ticks"] = memory["stable_ticks"] + 1 if t_moved <= STABLE_POS_TOLERANCE else 0
        else:
            memory["stable_ticks"] = 0

        # Damage tracking
        if memory["target_id"] == target_id and not blocked and abs(aim_error) < AIM_THRESHOLD:
            if target_health >= memory["target_health"] - 0.2:
                memory["no_damage_ticks"] += 1
            else:
                memory["no_damage_ticks"] = 0
        else:
            memory["no_damage_ticks"] = 0

        # ---- Movement -------------------------------------------------------
        if escaping_nade:
            if memory["nade_escape_dir"] < 0:
                move_left()
            else:
                move_right()
            if nearest_nade_dist < 120.0:
                jetpack()

        elif fleeing and not seeking_medkit:
            # Run from superior enemy
            if memory["flee_dir"] < 0:
                move_left()
            else:
                move_right()
            if fuel > 15.0 and memory["fly_tick"] <= 0:
                jetpack()
                memory["fly_tick"] = FLY_COOLDOWN_TICKS
            # Parting shot
            if not blocked and abs(aim_error) < AIM_THRESHOLD:
                if ammo_cur <= 0:
                    reload()
                else:
                    shoot()
                    did_attack = True
            # Parting grenade
            if not blocked and distance < 320.0 and memory["grenade_tick"] <= 0 and abs(aim_error) < AIM_THRESHOLD * 2:
                want_nade = None
                if grenades["gas"]    > 0: want_nade = 3
                elif grenades["frag"] > 0: want_nade = 1
                elif grenades["proxy"] > 0: want_nade = 2
                if want_nade is not None:
                    if grenades["selected_type"] != want_nade:
                        change_grenade_type()
                    else:
                        throw_grenade()
                        memory["grenade_tick"] = GRENADE_COOLDOWN_TICKS
                        did_attack = True

        elif not seeking_medkit:
            # ---- AGGRESSIVE HUNT / FIGHT ----------------------------------
            if blocked:
                # Bounce directions quickly to find line-of-sight
                if memory["evade_ticks"] <= 0:
                    memory["evade_dir"]   = -memory["evade_dir"]
                    memory["evade_ticks"] = 30   # shorter bounce (was 50)
                memory["evade_ticks"] -= 1
                if memory["evade_dir"] == -1:
                    move_left()
                else:
                    move_right()
                if memory["evade_ticks"] == 15:
                    jetpack()

            else:
                # Always charge — no backing off for weaker targets.
                # For stronger targets we still pressure hard.
                if distance > HUNT_CLOSE_DIST:
                    if dx < 0:
                        move_left()
                    else:
                        move_right()
                else:
                    # At melee range: strafe to dodge return fire
                    if memory["strafe_ticks"] <= 0:
                        memory["strafe_dir"]   = -memory["strafe_dir"]
                        memory["strafe_ticks"] = 40   # fast strafe
                    memory["strafe_ticks"] -= 1
                    if memory["strafe_dir"] == -1:
                        move_left()
                    else:
                        move_right()

            # Aggressive jetpack: chase if target is above OR we need to close fast
            if fuel > 8.0 and memory["fly_tick"] <= 0:
                should_fly = (dy < -15.0) or (distance > MAX_FIGHT_DIST) or blocked
                if should_fly:
                    jetpack()
                    memory["fly_tick"] = FLY_COOLDOWN_TICKS

            # Fire as fast as possible
            if not blocked and abs(aim_error) < AIM_THRESHOLD:
                if ammo_cur <= 0:
                    reload()
                else:
                    shoot()
                    did_attack = True
            elif ammo_cur <= 0:
                reload()

            # Grenade: throw early and often at weaker targets
            nade_range = 350.0 if hunt_target is not None else 320.0
            if (
                not escaping_nade and not blocked
                and distance < nade_range
                and (memory["stable_ticks"] >= STABLE_TICKS_TO_THROW or memory["no_damage_ticks"] >= 8)
                and memory["grenade_tick"] <= 0
            ):
                want_nade = None
                if grenades["gas"]    > 0: want_nade = 3
                elif grenades["frag"] > 0: want_nade = 1
                elif grenades["proxy"] > 0: want_nade = 2
                if want_nade is not None:
                    if grenades["selected_type"] != want_nade:
                        change_grenade_type()
                    else:
                        throw_grenade()
                        memory["grenade_tick"] = GRENADE_COOLDOWN_TICKS
                        did_attack = True

            # Low-health dodge
            if health < 30.0 and memory["dodge_tick"] <= 0:
                jetpack()
                memory["dodge_tick"] = 25

        memory["target_id"]     = target_id
        memory["target_health"] = target_health
        memory["target_x"]      = ex
        memory["target_y"]      = ey
        memory["hunt_id"]       = target_id if hunt_target is not None else memory["hunt_id"]

    # -----------------------------------------------------------------------
    # MARKER PURSUIT — no enemies in sensor, but we know where players are
    # Aggressively pathfind toward every marker, preferring previously weak ones
    # -----------------------------------------------------------------------
    elif markers and not seeking_medkit:
        # Always chase — pick closest marker (all players are worth hunting)
        marker  = min(markers, key=lambda m: m["distance"])
        m_angle = float(marker["angle"])
        m_dist  = float(marker["distance"])

        m_error = m_angle - current_aim
        if m_error >  math.pi: m_error -= 2.0 * math.pi
        if m_error < -math.pi: m_error += 2.0 * math.pi

        if m_error > 0.01:
            aim_right()
        elif m_error < -0.01:
            aim_left()

        # Move toward marker using cosine of angle
        if math.cos(m_angle) < 0:
            move_left()
        else:
            move_right()

        # Climb aggressively if marker is above
        if (m_angle < -0.15 and m_angle > -2.95) and fuel > 5.0:
            jetpack()
            memory["fly_tick"] = FLY_COOLDOWN_TICKS

        # Shoot opportunistically if line-of-sight is clear
        m_obstacle = state.distance_to_obstacle(m_angle, max_distance=2000.0, step=4.0)
        m_blocked  = m_obstacle < max(0.0, m_dist - 20.0)
        if not m_blocked and abs(m_error) < AIM_THRESHOLD:
            if ammo_cur <= 0:
                reload()
            else:
                shoot()
                did_attack = True
        elif ammo_cur <= 0:
            reload()

        memory["target_id"]       = int(marker["id"])
        memory["no_damage_ticks"] = 0
        memory["stable_ticks"]    = 0
        memory["flee_ticks"]      = 0

    # -----------------------------------------------------------------------
    # ROAM — no enemies, no markers: sweep the map fast
    # -----------------------------------------------------------------------
    else:
        memory["target_id"]       = -1
        memory["target_health"]   = -1.0
        memory["no_damage_ticks"] = 0
        memory["stable_ticks"]    = 0
        memory["flee_ticks"]      = 0

        front_angle = math.pi if memory["roam_dir"] == -1 else 0.0
        front_dist  = state.distance_to_obstacle(front_angle, max_distance=64.0, step=4.0)
        if front_dist < 22.0 or memory["roam_ticks"] <= 0:
            memory["roam_dir"]   = -memory["roam_dir"]
            memory["roam_ticks"] = 180   # shorter roam cycle = covers map faster
            jetpack()

        memory["roam_ticks"] -= 1

        if memory["roam_dir"] == -1:
            move_left()
        else:
            move_right()

        # Sweep aim toward direction of travel
        roam_aim_target = math.pi if memory["roam_dir"] == -1 else 0.0
        roam_aim_err    = roam_aim_target - current_aim
        if roam_aim_err >  math.pi: roam_aim_err -= 2.0 * math.pi
        if roam_aim_err < -math.pi: roam_aim_err += 2.0 * math.pi
        if memory["roam_ticks"] % 8 == 0:
            if roam_aim_err > 0.05:
                aim_right()
            elif roam_aim_err < -0.05:
                aim_left()

        # Hop platforms more frequently to scan terrain
        if memory["roam_ticks"] % 40 == 0:
            jetpack()

    # -----------------------------------------------------------------------
    # Anti-stuck: force reposition if we haven't moved
    # -----------------------------------------------------------------------
    moved     = math.sqrt((my_x - memory["last_x"])**2 + (my_y - memory["last_y"])**2)
    non_fight = (not enemies) and (not markers)

    if moved < 2.0 and ((not did_attack) or non_fight):
        memory["stuck_ticks"] += 1
    else:
        memory["stuck_ticks"] = 0

    stuck_limit = 18 if non_fight else 10   # less patience — reposition faster
    if memory["stuck_ticks"] >= stuck_limit:
        memory["roam_dir"] = -memory["roam_dir"]
        jetpack()
        memory["stuck_ticks"] = 0

    memory["last_x"] = my_x
    memory["last_y"] = my_y

    return memory