'''Recognize explicit teaching commands; questions never commit a step.'''
import re

START = {
    '开始第一步', '好的开始', '开始', '开始步骤', '开始化妆', '开始化妆吧',
    '我想开始步骤', '请带我一步一步做', '开始辅导', '带我开始步骤',
    'start', 'startroutine', 'letsstart', "let'sstart", 'iwanttostartthesteps',
}
ADVANCE = {
    '下一步', 'next', '继续', '继续吧', '我弄好了', '我做好了', '我完成了', '好我完成了',
    '我想开始下一步', '我想继续下一步', 'ifinishedthisstep', 'iwanttostartthenextstep',
    '我画好了继续', '画好了继续', '我已经做好了下一步呢', '已经做好了下一步',
}
FINISH = {
    '今天完成了', '好的今天完成了', '结束今天', '结束课程', '结束教学', '结束本次装扮',
    'finishsession', 'finishfortoday', 'endthelesson', 'finishthislook',
}
CONDITIONAL = ('如果', '假如', '要是', '能不能', '可不可以', '是否', '吗', '呢', 'how', 'whatif', 'canwe', 'cani', 'shouldi', 'shouldwe')
PROCEDURE = ('下一步', '开始', '跳过', '继续', '前一步', '上一步', '结束', '暂停', '保存',
             'next', 'start', 'skip', 'continue', 'previous', 'finish', 'pause', 'save')
NEGATIVE = ('不要', '不用', '不想', '别', '还没', '没画完', "don't", 'donot', 'notfinished',
            'notready', 'notskip', 'notstart', 'notadvance', 'notcontinue', 'neverskip')


def coaching_intent(text):
    value = re.sub(r'[\s，,。.!！?？]+', '', text.lower().replace('’', "'"))
    question = any(mark in text for mark in '?？') or any(term in value for term in CONDITIONAL)
    if any(term in value for term in ('不明白', '不太明白', '怎么上', '解释', 'explain')):
        return 'explain'
    if not question and (value.startswith(('等等', '暂停')) or text.casefold().startswith('wait,')):
        return 'pause'
    if any(term in value for term in NEGATIVE):
        return 'ambiguous' if any(term in value for term in ('下一步', '还没', '没画完', 'next', 'notfinished', 'notready')) else 'chat'
    if any(term in value for term in ('再说一遍', '再说一次', '重复', 'repeat')):
        return 'repeat'
    if value in {'slowdown', '慢一点', 'why', '为什么', '详细一点'}:
        return 'explain'
    if value in {'前一步怎么做的', '上一步怎么做的'}:
        return 'explain'
    if question:
        if value in {'我已经做好了下一步呢', '已经做好了下一步', '我画好了下一步呢'}:
            return 'advance'
        if any(term in value for term in PROCEDURE):
            return 'ambiguous'
    if value in {'checkthis', 'check', '检查', '相机检查', 'checkwithcamera'} or any(
        term in value for term in ('帮我看看', '帮我检查', '左右是不是一样', '调整好了', '重新检查', '再检查一次',
                                   '再看一次', '现在呢', '检查腮红', '检查唇', 'checkagain', 'checkmy', 'visualcheck')
    ):
        return 'visual'
    if value in {'跳过', '跳过这一步', 'skip', 'skipthisstep'}:
        return 'skip'
    if value in {'保存到我的记录', 'savethistomyrecords', 'savemyjournal'}:
        return 'save'
    if value in FINISH:
        return 'finish'
    if value in {'等等', '等一下', '暂停', 'wait', 'pause', 'pauselesson'}:
        return 'pause'
    if value in {'前一步', '上一步', 'previousstep'}:
        return 'previous'
    if value in {'现在画腮红', '开始画腮红', '我现在开始画腮红'}:
        return 'blush'
    if value in {'恢复', '继续通话', 'resumesession', 'resume'}:
        return 'resume'
    if value in START:
        return 'start'
    if value in ADVANCE:
        return 'advance'
    if any(term in value for term in ('下一步', '接下来', '然后呢', '准备好了', 'nextstep', 'whatsnext')):
        return 'ambiguous'
    return 'chat'
