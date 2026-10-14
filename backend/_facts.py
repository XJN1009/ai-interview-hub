"""提交材料数字复核脚本：只读统计题库种子与本地库实测口径。"""
import collections
import io
import re
import sqlite3

src = io.open('app/data/question_bank.py', encoding='utf-8').read()
rows = re.findall(
    r'"job_category":\s*"(.*?)",\s*"question_type":\s*"(.*?)",\s*"skill_name":\s*"(.*?)"', src)
print('SEED rows', len(rows))
print('SEED categories', len({r[0] for r in rows}))
print('SEED skills', len({r[2] for r in rows}))
print('SEED types', collections.Counter(r[1] for r in rows))

db = sqlite3.connect('zhimeicang.db')
q = db.execute
print('DB version', q('select version_num from alembic_version').fetchall())
print('DB total', q('select count(*) from question_bank').fetchone())
print('DB categories', q('select count(distinct job_category) from question_bank').fetchone())
print('DB skills', q('select count(distinct skill_name) from question_bank').fetchone())
print('DB types', q('select question_type, count(*) from question_bank group by 1').fetchall())
print('DB status', q('select review_status, count(*) from question_bank group by 1').fetchall())
print('DB batch', q('select batch, count(*) from question_bank group by 1 order by batch').fetchall())
print('DB tables', q("select count(*) from sqlite_master where type='table'").fetchone())
print('DB users/jobs/interviews',
      q('select (select count(*) from users), (select count(*) from jobs), '
        '(select count(*) from interviews)').fetchone())
print('reverse cols', [r[1] for r in q('pragma table_info(interview_reverse_question)')])
