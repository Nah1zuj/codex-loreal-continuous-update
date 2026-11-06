"""Conservative commands. Negation and questions take precedence over completion."""
import re

def coaching_intent(text):
    value=re.sub(r'[\s，,。.!！?？]+','',text.lower())
    if any(x in value for x in ('不要','不用','不想',"don't",'donot')):return 'chat'
    if value in {'checkthis','check','检查','相机检查','checkwithcamera'}:return 'visual'
    if value in {'slowdown','慢一点','why','为什么','详细一点'}:return 'explain'
    if value in {'跳过','跳过这一步','skip','skipthisstep'}:return 'skip'
    if value in {'保存到我的记录','savethistomyrecords','savemyjournal'} and not any(mark in text for mark in '?？'):return 'save'
    if any(x in value for x in ('今天完成了','结束今天','finishsession','finishfortoday')):return 'finish'
    if any(x in value for x in ('还没','没画完','等等','暂停','wait','notfinished','pause')):return 'pause'
    if any(x in value for x in ('前一步','上一步','previousstep')):return 'previous'
    if any(x in value for x in ('不明白','怎么上','解释','explain')):return 'explain'
    if any(x in value for x in ('再说一遍','重复','repeat')):return 'repeat'
    if any(x in value for x in ('帮我看看','帮我检查','左右是不是一样','调整好了','重新检查','再检查一次','再看一次','现在呢','检查腮红','检查唇','checkagain','checkmy','visualcheck')):return 'visual'
    if '腮红' in value and any(x in value for x in ('开始','现在画')):return 'blush'
    if value in {'恢复','继续通话','resumesession','resume'}:return 'resume'
    if value in {'开始第一步','好的开始','开始','开始步骤','开始化妆','start','startroutine','letsstart'}:return 'start'
    if value in {'下一步','next','继续','继续吧','然后呢','我准备好了','我们接下来做什么','我弄好了','我做好了','我完成了','好我完成了','我想开始下一步','ifinishedthisstep'} or any(x in value for x in ('画好了继续','已经做好了下一步')):return 'advance'
    return 'chat'
