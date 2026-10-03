#!/usr/bin/env python3
"""检查并操作 Google Chrome 中已获用户授权的 CMEChina 课程标签页。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlparse


APPLESCRIPT = r'''
on run argv
  set courseNeedle to item 1 of argv
  set jsCode to item 2 of argv
  tell application "Google Chrome"
    repeat with w in windows
      repeat with t in tabs of w
        try
          set u to URL of t
          if (u starts with "https://www.cmechina.net/" or u starts with "https://cmechina.net/") and (u contains (courseNeedle & "&") or u ends with courseNeedle or u contains (courseNeedle & "#")) then
            return execute t javascript jsCode
          end if
        end try
      end repeat
    end repeat
  end tell
  return "{\"error\":\"TAB_NOT_FOUND\"}"
end run
'''


SECTION_JS = r'''
  const sectionLinks=Array.from(document.querySelectorAll('a')).filter(a=>/^第\s*\d+\s*节/.test((a.innerText||'').trim()));
  const sectionRow=a=>{
    let node=a;
    for(let depth=0;node&&depth<5;depth++,node=node.parentElement){
      const text=(node.innerText||'').trim();
      if(/未学习|考试通过|未通过|未考试|学习中|已学习/.test(text))return text;
    }
    return '';
  };
  const seenSections=new Set();
  const courseSections=sectionLinks.flatMap(a=>{
    const jump=(a.getAttribute('onclick')||'').match(/kjJumpTo\('([^']+)'/);
    const url=new URL(jump?jump[1]:a.href,location.href);
    const id=url.searchParams.get('courseware_id');
    if(url.searchParams.get('course_id')!==new URL(location.href).searchParams.get('course_id')||!id||seenSections.has(id))return [];
    seenSections.add(id);
    const text=sectionRow(a);
    return [{id,label:(a.innerText||'').trim(),url:url.href,text,passed:/考试通过/.test(text)&&!/未通过/.test(text)}];
  });
'''

STATUS_JS = r'''JSON.stringify((()=>{
  const text=document.body?.innerText||'';
  const v=document.querySelector('video');
  const path=location.pathname;
  const page=path.includes('study2.jsp')?'video':path.includes('examCoursePass.jsp')?'course-pass':path.includes('examQuizPass.jsp')?'pass':path.includes('examQuizFail.jsp')?'fail':path.includes('exam.jsp')?'exam':path.includes('course.jsp')?'course':'other';
  const visible=e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&e.getClientRects().length>0};
  const popupSelectors='[role="dialog"],[aria-modal="true"],.layui-layer,.modal,.modal-dialog,.el-dialog,.ant-modal,.ui-dialog,.popup,.pop-up';
  const popupCandidates=Array.from(document.querySelectorAll(popupSelectors)).filter(visible);
  const popupRoots=popupCandidates.filter(e=>!popupCandidates.some(other=>other!==e&&e.contains(other)));
  const protectedPopupPattern=/(人脸|身份|实名|登录|验证码|密码|本人(?:操作|确认|完成|签到)|学员本人|提交考卷|提交答案|支付|付款|购买|授权|同意协议|学习承诺|播放行为异常)/;
  const protectedPopup=popupRoots.map(e=>(e.innerText||'').trim()).find(t=>protectedPopupPattern.test(t))||null;
  const sections=Array.from(document.querySelectorAll('#s_r_ml li')).map(li=>({text:(li.innerText||'').trim(),className:li.className}));
  /* SECTION_DATA */
  return {
    page,url:location.href,title:document.title,
    video:v?{time:v.currentTime,duration:v.duration,paused:v.paused,ended:v.ended,rate:v.playbackRate,armed:v.dataset.codexEndedExamArmed||null}:null,
    action:document.documentElement.dataset.codexEndedExamAction||null,
    abnormal:text.includes('播放行为异常'),
    signin:Array.from(document.querySelectorAll('*')).some(e=>(e.innerText||'').trim()==='签到'&&visible(e)),
    popup:{
      visible:popupRoots.length,
      protected:document.documentElement.dataset.codexProtectedPopup||protectedPopup,
      lastAction:document.documentElement.dataset.codexPopupAction||null,
      summaries:popupRoots.slice(0,5).map(e=>(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,300))
    },
    questions:document.querySelectorAll('h3.name').length,
    rightRate:new URL(location.href).searchParams.get('rightRate'),
    sections,
    progress:page==='course'?{total:courseSections.length,passed:courseSections.filter(s=>s.passed).length,allPassed:courseSections.length>0&&courseSections.every(s=>s.passed),sections:courseSections}:null,
    summary:text.slice(0,5000)
  };
})())'''.replace('/* SECTION_DATA */', SECTION_JS)


def popup_tools_js(*, watch: bool = False) -> str:
    watch_literal = "true" if watch else "false"
    return rf'''
      const popupTools=(()=>{{
        const visible=e=>{{if(!e)return false;const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&e.getClientRects().length>0}};
        const selectors='[role="dialog"],[aria-modal="true"],.layui-layer,.modal,.modal-dialog,.el-dialog,.ant-modal,.ui-dialog,.popup,.pop-up';
        const protectedPattern=/(人脸|身份|实名|登录|验证码|密码|本人(?:操作|确认|完成|签到)|学员本人|提交考卷|提交答案|支付|付款|购买|授权|同意协议|学习承诺|播放行为异常)/;
        const dangerousPattern=/(登录|验证|提交|支付|付款|购买|授权|同意|开始考试|进入考试)/;
        const safePattern=/^(关闭|签到|取消|稍后|暂不|以后再说|知道了|我知道了|好的|好|确定|确认|继续播放|继续观看|OK|×|✕)$/i;
        const label=e=>(e.innerText||e.value||e.getAttribute('aria-label')||e.getAttribute('title')||'').trim();
        const roots=()=>{{
          const candidates=Array.from(document.querySelectorAll(selectors)).filter(visible);
          return candidates.filter(e=>!candidates.some(other=>other!==e&&e.contains(other)));
        }};
        const protectedRoot=root=>protectedPattern.test((root.innerText||'').trim());
        const control=root=>{{
          const items=Array.from(root.querySelectorAll('button,a,input[type=button],input[type=submit],[role=button],[aria-label],[title]')).filter(visible);
          return items.find(e=>{{
            const t=label(e);
            const closeHint=/(^|[-_ ])close($|[-_ ])|关闭/.test(String(e.className||''))||/^(关闭|close)$/i.test(e.getAttribute('aria-label')||e.getAttribute('title')||'');
            return (closeHint||safePattern.test(t))&&!dangerousPattern.test(t);
          }})||null;
        }};
        const dismiss=()=>{{
          const result={{dismissed:[],blocked:[],unhandled:[]}};
          const popupRoots=roots();
          for(const root of popupRoots){{
            const summary=(root.innerText||root.getAttribute('aria-label')||'').trim().slice(0,300);
            if(protectedRoot(root)){{result.blocked.push(summary);continue;}}
            const e=control(root);
            if(!e){{result.unhandled.push(summary);continue;}}
            const button=label(e)||'close-control';
            e.click();
            result.dismissed.push({{button,summary}});
          }}
          const standaloneSignin=Array.from(document.querySelectorAll('button,a,input[type=button],input[type=submit],[role=button]')).find(e=>label(e)==='签到'&&visible(e)&&!e.closest(selectors));
          if(standaloneSignin){{
            standaloneSignin.click();
            result.dismissed.push({{button:'签到',summary:'standalone-signin-marker'}});
          }}
          const html=document.documentElement;
          html.dataset.codexPopupAction=JSON.stringify(result).slice(0,2000);
          if(result.blocked.length)html.dataset.codexProtectedPopup=result.blocked.join(' | ').slice(0,1000);
          else delete html.dataset.codexProtectedPopup;
          return result;
        }};
        const install=()=>{{
          if(window.__codexPopupObserver)return false;
          let timer=0;
          window.__codexPopupObserver=new MutationObserver(()=>{{
            clearTimeout(timer);
            timer=setTimeout(dismiss,150);
          }});
          window.__codexPopupObserver.observe(document.documentElement,{{childList:true,subtree:true,attributes:true,attributeFilter:['class','style','open','aria-hidden']}});
          return true;
        }};
        return {{dismiss,install,roots}};
      }})();
      const popupResult=popupTools.dismiss();
      const popupWatching={watch_literal}?popupTools.install():false;
    '''


def dismiss_js(*, watch: bool = False) -> str:
    tools = popup_tools_js(watch=watch)
    return rf'''JSON.stringify((()=>{{
      {tools}
      return {{ok:popupResult.blocked.length===0,error:popupResult.blocked.length?'PROTECTED_POPUP':null,popup:popupResult,watching:popupWatching||Boolean(window.__codexPopupObserver),url:location.href}};
    }})())'''


EXAM_JS = r'''JSON.stringify((()=>({
  url:location.href,
  title:document.title,
  questions:Array.from(document.querySelectorAll('h3.name')).map((h,index)=>({
    index:index+1,
    text:(h.innerText||'').trim(),
    options:Array.from(h.parentElement.querySelectorAll('input[type=radio]')).map(e=>({
      name:e.name,value:e.value,text:(e.parentElement?.innerText||'').trim(),checked:e.checked
    }))
  }))
}))())'''


def arm_js(resume: bool) -> str:
    resume_literal = "true" if resume else "false"
    tools = popup_tools_js(watch=True)
    return rf'''JSON.stringify((()=>{{
      {tools}
      const v=document.querySelector('video');
      if(popupResult.blocked.length){{
        if(v&&!v.paused)v.pause();
        return {{ok:false,error:'PROTECTED_POPUP',popup:popupResult,url:location.href}};
      }}
      if(!v)return {{ok:false,error:'NO_VIDEO',popup:popupResult,url:location.href}};
      const visible=e=>{{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&e.getClientRects().length>0}};
      const go=()=>{{
        const root=document.documentElement;
        if(root.dataset.codexEndedExamAction==='clicked'||root.dataset.codexEndedExamPending==='1')return;
        root.dataset.codexEndedExamPending='1';
        let tries=0;
        const findAndClick=()=>{{
          const e=Array.from(document.querySelectorAll('a,button,input')).find(x=>(x.innerText||x.value||'').trim()==='本节考试'&&visible(x));
          if(e){{
            root.dataset.codexEndedExamFired='1';
            root.dataset.codexEndedExamAction='clicked';
            delete root.dataset.codexEndedExamPending;
            e.click();
            return;
          }}
          tries+=1;
          if(tries<5){{
            root.dataset.codexEndedExamAction='waiting';
            setTimeout(findAndClick,1500);
          }} else {{
            root.dataset.codexEndedExamAction='not_found';
            delete root.dataset.codexEndedExamPending;
          }}
        }};
        setTimeout(findAndClick,1500);
      }};
      if(v.dataset.codexEndedExamArmed!=='1'){{
        v.dataset.codexEndedExamArmed='1';
        v.addEventListener('ended',go,{{once:true}});
      }}
      v.playbackRate=1;
      if({resume_literal}&&!v.ended&&v.paused)v.play().catch(()=>{{}});
      if(v.ended)go();
      return {{ok:true,url:location.href,time:v.currentTime,duration:v.duration,paused:v.paused,ended:v.ended,rate:v.playbackRate,armed:v.dataset.codexEndedExamArmed,popup:popupResult,popupWatching:Boolean(window.__codexPopupObserver)}};
    }})())'''


def select_js(answers: list[str]) -> str:
    payload = json.dumps(answers, ensure_ascii=False)
    return rf'''JSON.stringify((()=>{{
      const answers={payload};
      const groups=Array.from(new Set(Array.from(document.querySelectorAll('input[type=radio]')).map(e=>e.name)));
      if(groups.length!==answers.length)return {{ok:false,error:'ANSWER_COUNT_MISMATCH',questions:groups.length,answers:answers.length}};
      for(let i=0;i<groups.length;i++){{
        const value=String(answers[i]).toUpperCase();
        const e=Array.from(document.querySelectorAll('input[type=radio]')).find(x=>x.name===groups[i]&&x.value===value);
        if(!e)return {{ok:false,error:'OPTION_NOT_FOUND',question:i+1,value}};
        e.click();
      }}
      return {{ok:true,selections:groups.map((name,index)=>({{index:index+1,name,value:Array.from(document.querySelectorAll('input[type=radio]')).find(x=>x.name===name&&x.checked)?.value||null}}))}};
    }})())'''


SUBMIT_JS = r'''JSON.stringify((()=>{
  if(!location.pathname.endsWith('/exam.jsp'))return {ok:false,error:'NOT_ON_EXAM'};
  const radios=Array.from(document.querySelectorAll('input[type=radio]'));
  const groups=Array.from(new Set(radios.map(e=>e.name)));
  if(!groups.length)return {ok:false,error:'NO_QUESTIONS'};
  const missing=groups.filter(name=>!radios.some(e=>e.name===name&&e.checked));
  if(missing.length)return {ok:false,error:'UNANSWERED',missing};
  const e=document.getElementById('tjkj')||Array.from(document.querySelectorAll('a,button,input')).find(x=>(x.innerText||x.value||'').trim()==='提交考卷');
  if(!e)return {ok:false,error:'SUBMIT_NOT_FOUND'};
  const selections=groups.map(name=>({name,value:radios.find(x=>x.name===name&&x.checked)?.value||null}));
  e.click();
  return {ok:true,action:'submitted',selections};
})())'''


RETRY_JS = r'''JSON.stringify((()=>{
  if(!location.pathname.includes('examQuizFail.jsp'))return {ok:false,error:'NOT_ON_FAILED_EXAM',url:location.href};
  const visible=e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&e.getClientRects().length>0};
  const e=Array.from(document.querySelectorAll('a,button,input')).find(x=>(x.innerText||x.value||'').trim()==='重新答题'&&visible(x));
  if(!e)return {ok:false,error:'RETRY_NOT_FOUND'};
  e.click();
  return {ok:true,action:'retry'};
})())'''


ADVANCE_JS = r'''JSON.stringify((()=>{
  const exact=label=>Array.from(document.querySelectorAll('a,button,input')).find(e=>(e.innerText||e.value||'').trim()===label);
  const path=location.pathname;
  if(path.includes('examCoursePass.jsp')){
    const id=new URL(location.href).searchParams.get('course_id');
    if(!id||!/^\d+$/.test(id))return {ok:false,error:'COURSE_ID_MISSING'};
    location.href='/cme/course.jsp?course_id='+id;
    return {ok:true,action:'verify-course'};
  }
  if(path.includes('examQuizPass.jsp')){
    const e=exact('继续学习下一节');
    if(!e)return {ok:false,error:'CONTINUE_NOT_FOUND'};
    e.click();return {ok:true,action:'continue'};
  }
  if(path.includes('course.jsp')){
    /* SECTION_DATA */
    if(!courseSections.length)return {ok:false,error:'SECTION_LIST_MISSING'};
    if(courseSections.every(s=>s.passed))return {ok:true,action:'complete',total:courseSections.length};
    const next=courseSections.find(s=>!s.passed);
    if(!next.text)return {ok:false,error:'SECTION_STATUS_UNKNOWN',section:next};
    const e=sectionLinks.find(a=>{
      const jump=(a.getAttribute('onclick')||'').match(/kjJumpTo\('([^']+)'/);
      return new URL(jump?jump[1]:a.href,location.href).href===next.url;
    });
    if(!e)return {ok:false,error:'SECTION_LINK_MISSING',section:next};
    e.click();return {ok:true,action:'enter-section',section:next};
  }
  if(path.includes('study2.jsp')){
    const v=document.querySelector('video');
    if(!v?.ended)return {ok:false,error:'VIDEO_NOT_ENDED'};
    const e=exact('本节考试');
    if(!e)return {ok:false,error:'EXAM_NOT_FOUND'};
    e.click();return {ok:true,action:'exam'};
  }
  return {ok:false,error:'NO_ADVANCE_ACTION',url:location.href};
})())'''.replace('/* SECTION_DATA */', SECTION_JS)


def course_id_from_url(value: str) -> str:
    url = urlparse(value)
    if url.scheme != 'https' or url.hostname not in {'cmechina.net', 'www.cmechina.net'} or url.username or url.password or url.port not in {None, 443}:
        raise ValueError('请提供 HTTPS CMEChina 课程网页地址')
    ids = parse_qs(url.query).get('course_id', [])
    if len(ids) != 1 or not re.fullmatch(r'\d+', ids[0]):
        raise ValueError('网址必须包含唯一的数字 course_id')
    return ids[0]


def run_js(course_id: str, javascript: str) -> object:
    if not re.fullmatch(r"\d+", course_id):
        raise ValueError("课程 ID 只能包含数字")
    proc = subprocess.run(
        ["osascript", "-e", APPLESCRIPT, "--", f"course_id={course_id}", javascript],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"osascript 异常退出，代码为 {proc.returncode}")
    raw = proc.stdout.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--course-id", help="数字格式的 CMEChina course_id")
    source.add_argument("--url", help="用户提供的 CMEChina 课程网页地址")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="检查匹配的课程标签页")
    dismiss = sub.add_parser("dismiss", help="消除普通站内弹窗并报告需要本人处理的受保护弹窗")
    dismiss.add_argument("--watch", action="store_true", help="持续观察并消除当前页面后续出现的普通弹窗")
    arm = sub.add_parser("arm", help="挂载视频结束事件监听器")
    arm.add_argument("--resume", action="store_true", help="恢复播放尚未结束但已暂停的视频")
    sub.add_parser("exam", help="提取当前考试的题目与选项")
    select = sub.add_parser("select", help="为每道题选择答案，但不提交")
    select.add_argument("--answers", required=True, help="按题目顺序提供逗号分隔的选项字母")
    sub.add_parser("submit", help="提交已经全部作答的当前试卷")
    sub.add_parser("retry", help="在已核实错误反馈后重新进入未通过的考试")
    sub.add_parser("advance", help="在当前状态完成后执行正常的下一步操作")
    args = parser.parse_args()
    args.course_id = course_id_from_url(args.url) if args.url else args.course_id

    if args.command == "status":
        result = run_js(args.course_id, STATUS_JS)
    elif args.command == "dismiss":
        result = run_js(args.course_id, dismiss_js(watch=args.watch))
    elif args.command == "arm":
        result = run_js(args.course_id, arm_js(args.resume))
    elif args.command == "exam":
        result = run_js(args.course_id, EXAM_JS)
    elif args.command == "select":
        answers = [x.strip().upper() for x in args.answers.split(",") if x.strip()]
        if not answers or any(not re.fullmatch(r"[A-Z]", x) for x in answers):
            parser.error("--answers 必须是以逗号分隔的选项字母，例如 A,C,B")
        result = run_js(args.course_id, select_js(answers))
    elif args.command == "submit":
        result = run_js(args.course_id, SUBMIT_JS)
    elif args.command == "retry":
        result = run_js(args.course_id, RETRY_JS)
    else:
        result = run_js(args.course_id, ADVANCE_JS)

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not (isinstance(result, dict) and result.get("error")) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
