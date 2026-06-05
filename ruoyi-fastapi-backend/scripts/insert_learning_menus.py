"""
向 sys_menu 插入「反身性研究」侧边栏菜单，并关联到学生(3)、教师(4)角色
"""
import asyncio
import asyncpg


async def insert_menus():
    conn = await asyncpg.connect(
        host='115.220.6.150', port=15432,
        user='weifuqiang', password='weifuqiang',
        database='ruoyi-fastapi',
    )

    try:
        now = 'NOW()'

        # 先清理旧数据（幂等）
        await conn.execute("DELETE FROM sys_role_menu WHERE menu_id >= 4000 AND menu_id < 5000")
        await conn.execute("DELETE FROM sys_menu WHERE menu_id >= 4000 AND menu_id < 5000")

        # ============================================================
        # 1. 顶层目录: 反身性研究
        # ============================================================
        await conn.execute("""
            INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name,
                                  is_frame, is_cache, menu_type, visible, status, perms, icon,
                                  create_by, create_time)
            VALUES (4000, '反身性研究', 0, 7, 'learning', NULL, NULL, 1, 0, 'M', '0', '0', '', 'education', 'admin', NOW())
        """)

        # ============================================================
        # 2. 学生端菜单
        # ============================================================
        await conn.execute("""
            INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name,
                                  is_frame, is_cache, menu_type, visible, status, perms, icon,
                                  create_by, create_time)
            VALUES (4100, '我的任务', 4000, 1, 'my-tasks', 'learning/task/StudentTaskList', NULL, 1, 0, 'C', '0', '0', 'learning:task:student:list', 'list', 'admin', NOW())
        """)

        await conn.execute("""
            INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name,
                                  is_frame, is_cache, menu_type, visible, status, perms, icon,
                                  create_by, create_time)
            VALUES (4101, '我的研究记录', 4000, 2, 'my-records', 'learning/record/MyRecordList', NULL, 1, 0, 'C', '0', '0', 'learning:record:my', 'log', 'admin', NOW())
        """)

        # ============================================================
        # 3. 教师端菜单
        # ============================================================
        await conn.execute("""
            INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name,
                                  is_frame, is_cache, menu_type, visible, status, perms, icon,
                                  create_by, create_time)
            VALUES (4200, '教学任务管理', 4000, 1, 'task-manage', 'learning/task/TeacherTaskManager', NULL, 1, 0, 'C', '0', '0', 'learning:task:list', 'form', 'admin', NOW())
        """)

        await conn.execute("""
            INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name,
                                  is_frame, is_cache, menu_type, visible, status, perms, icon,
                                  create_by, create_time)
            VALUES (4201, '班级研究监控', 4000, 2, 'class-monitor', 'learning/monitor/ClassOverview', NULL, 1, 0, 'C', '0', '0', 'learning:monitor:class', 'chart', 'admin', NOW())
        """)

        await conn.execute("""
            INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name,
                                  is_frame, is_cache, menu_type, visible, status, perms, icon,
                                  create_by, create_time)
            VALUES (4202, '评价管理', 4000, 3, 'evaluation', 'learning/monitor/EvaluationForm', NULL, 1, 0, 'C', '0', '0', 'learning:evaluation:submit', 'star', 'admin', NOW())
        """)

        await conn.execute("""
            INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name,
                                  is_frame, is_cache, menu_type, visible, status, perms, icon,
                                  create_by, create_time)
            VALUES (4203, '优秀案例库', 4000, 4, 'cases', 'learning/case/CaseList', NULL, 1, 0, 'C', '0', '0', 'learning:case:list', 'medal', 'admin', NOW())
        """)

        # ============================================================
        # 4. 角色菜单关联
        # ============================================================

        # 管理员(role_id=1): 所有菜单
        for mid in [4000, 4100, 4101, 4200, 4201, 4202, 4203]:
            await conn.execute("INSERT INTO sys_role_menu (role_id, menu_id) VALUES (1, $1)", mid)

        # 学生(role_id=3): 顶层目录 + 学生菜单
        for mid in [4000, 4100, 4101]:
            await conn.execute("INSERT INTO sys_role_menu (role_id, menu_id) VALUES (3, $1)", mid)

        # 教师(role_id=4): 顶层目录 + 教师菜单
        for mid in [4000, 4200, 4201, 4202, 4203]:
            await conn.execute("INSERT INTO sys_role_menu (role_id, menu_id) VALUES (4, $1)", mid)

        # 验证
        menus = await conn.fetch("""
            SELECT m.menu_id, m.menu_name, m.parent_id, m.path, m.component, m.menu_type
            FROM sys_menu m
            WHERE m.menu_id >= 4000 AND m.menu_id < 5000
            ORDER BY m.menu_id
        """)
        print("Menus inserted:")
        for m in menus:
            prefix = "  +" if m['parent_id'] == 0 else "    +"
            print(f"{prefix} id={m['menu_id']}, {m['menu_name']}, path={m['path']}, comp={m['component']}")

        print("\nRole assignments:")
        for role_id, role_name in [(1, 'admin'), (3, 'student'), (4, 'teacher')]:
            ids = await conn.fetch("""
                SELECT menu_id FROM sys_role_menu
                WHERE role_id = $1 AND menu_id >= 4000 AND menu_id < 5000
                ORDER BY menu_id
            """, role_id)
            menu_names = []
            for r in ids:
                n = await conn.fetchval("SELECT menu_name FROM sys_menu WHERE menu_id = $1", r['menu_id'])
                menu_names.append(n)
            print(f"  {role_name}(role_id={role_id}): {', '.join(menu_names)}")

        print("\nDone! Please refresh the browser page to see the new sidebar menu.")

    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(insert_menus())
