"""离线行为测试：不点击或提交真实课程。运行 python3 本文件。"""

import json
import subprocess
import unittest

import cmechina_chrome as runner


def evaluate(script, rows=(), path='/cme/course.jsp', radios=()):
    fixture = json.dumps({'rows': rows, 'path': path, 'radios': radios})
    harness = r'''
const fixture=FIXTURE;
global.location={href:'https://www.cmechina.net'+fixture.path+'?course_id=123',pathname:fixture.path};
global.getComputedStyle=()=>({display:'block',visibility:'visible'});
const links=fixture.rows.map(row=>{
 const parent={innerText:row.text,parentElement:null};
 return {innerText:row.label,href:'https://www.cmechina.net/cme/study2.jsp?course_id='+(row.course||'123')+'&courseware_id='+row.id,parentElement:parent,getAttribute(name){return name==='onclick'&&row.onclick?row.onclick:null;},click(){global.clicked=row.onclick?row.onclick.match(/kjJumpTo\('([^']+)'/)[1]:this.href;}};
});
global.document={title:'测试课程',body:{innerText:'测试课程'},documentElement:{dataset:{}},getElementById:()=>null,
 querySelector:()=>null,querySelectorAll(selector){
 if(selector==='a')return links;
 if(selector==='input[type=radio]')return fixture.radios;
 return [];
 }};
const result=eval(SCRIPT);
process.stdout.write(JSON.stringify({result:JSON.parse(result),clicked:global.clicked||null,url:location.href}));
'''.replace('FIXTURE', fixture).replace('SCRIPT', json.dumps(script))
    result = subprocess.run(['node', '-e', harness], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


class CourseTests(unittest.TestCase):
    def test_url_input(self):
        self.assertEqual(runner.course_id_from_url('https://www.cmechina.net/cme/study2.jsp?course_id=123&courseware_id=02'), '123')
        for url in ['https://cmechina.net.evil.test/?course_id=123', 'http://www.cmechina.net/?course_id=123', 'https://www.cmechina.net/?course_id=1&course_id=2', 'https://www.cmechina.net/?course_id=abc']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                runner.course_id_from_url(url)

    def test_empty_list_not_complete(self):
        self.assertFalse(evaluate(runner.STATUS_JS)['result']['progress']['allPassed'])
        self.assertEqual(evaluate(runner.ADVANCE_JS)['result']['error'], 'SECTION_LIST_MISSING')

    def test_complete_without_click(self):
        rows = [{'label': '第01节 入门', 'id': '01', 'text': '第01节 入门 考试通过'}]
        self.assertTrue(evaluate(runner.STATUS_JS, rows)['result']['progress']['allPassed'])
        result = evaluate(runner.ADVANCE_JS, rows)
        self.assertEqual(result['result']['action'], 'complete')
        self.assertIsNone(result['clicked'])

    def test_tenth_section_and_deduplicate(self):
        rows = [
            {'label': '第01节 入门', 'id': '01', 'text': '考试通过'},
            {'label': '第10节 进阶', 'id': '10', 'text': '已学习 未考试'},
            {'label': '第10节 进阶', 'id': '10', 'text': '已学习 未考试'},
            {'label': '第11节 别的课程', 'id': '11', 'course': '999', 'text': '未学习'},
        ]
        status = evaluate(runner.STATUS_JS, rows)['result']['progress']
        self.assertEqual((status['total'], status['passed'], status['allPassed']), (2, 1, False))
        result = evaluate(runner.ADVANCE_JS, rows)
        self.assertEqual(result['result']['section']['id'], '10')
        self.assertIn('courseware_id=10', result['clicked'])

    def test_onclick_navigation(self):
        target = 'https://www.cmechina.net/cme/study2.jsp?course_id=123&courseware_id=02'
        rows = [{'label': '第02节 继续', 'id': '02', 'text': '未学习', 'onclick': "kjJumpTo('" + target + "')"}]
        self.assertEqual(evaluate(runner.ADVANCE_JS, rows)['clicked'], target)

    def test_unknown_status_stops(self):
        rows = [{'label': '第02节 未知状态', 'id': '02', 'text': '加载中'}]
        self.assertEqual(evaluate(runner.ADVANCE_JS, rows)['result']['error'], 'SECTION_STATUS_UNKNOWN')

    def test_final_result_requires_verification(self):
        self.assertEqual(evaluate(runner.STATUS_JS, path='/cme/examCoursePass.jsp')['result']['page'], 'course-pass')
        result = evaluate(runner.ADVANCE_JS, path='/cme/examCoursePass.jsp')
        self.assertEqual(result['result']['action'], 'verify-course')
        self.assertEqual(result['url'], '/cme/course.jsp?course_id=123')

    def test_submit_rejects_wrong_page_empty_and_unanswered(self):
        self.assertEqual(evaluate(runner.SUBMIT_JS)['result']['error'], 'NOT_ON_EXAM')
        self.assertEqual(evaluate(runner.SUBMIT_JS, path='/cme/exam.jsp')['result']['error'], 'NO_QUESTIONS')
        self.assertEqual(evaluate(runner.SUBMIT_JS, path='/cme/exam.jsp', radios=[{'name': 'q1', 'checked': False}])['result']['error'], 'UNANSWERED')


if __name__ == '__main__':
    unittest.main()
