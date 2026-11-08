import pytest
from app.agent.coaching_intents import coaching_intent

@pytest.mark.parametrize('text,expected',[
    ('开始第一步。','start'),('好的，开始。','start'),
    ('下一步。','advance'),('我画好了，继续。','advance'),
    ('我已经做好了，下一步呢？','advance'),('好，我完成了。','advance'),
    ('你能再说一遍吗？','repeat'),('等等，我还没画完。','pause'),
    ('前一步怎么做的？','explain'),('帮我看看现在怎么样。','visual'),
    ('现在我调整好了。','visual'),('好的，今天完成了。','finish'),
    ('保存到我的记录。','save'),('我现在开始画腮红。','blush'),
    ('再检查一次。','visual'),('重复一下。','repeat'),('我还没有完成。','ambiguous'),('不要再检查一次。','chat'),('Tell me about the rain','chat'),('I finished this step.','advance'),
])
def test_contextual_intents(text,expected):
    assert coaching_intent(text)==expected
