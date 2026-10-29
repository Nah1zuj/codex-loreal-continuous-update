def accessible_result(result, settings):
    prefix = '【模拟演示，不是实际摄像观察】' if result.get('simulated') else ''
    if result['confidence'] < settings.confidence_min or result['status']=='UNCERTAIN':
        return prefix+'现在的信息还不够清楚，我不想随便猜。可以调整光线或把脸转正，再试一次。'
    states = {'BOTH':'你左右两侧面颊都有可见腮红','NO_BLUSH':'目前没有明确确认到腮红','LEFT_ONLY':'你左侧面颊有可见腮红，右侧尚未明确确认','RIGHT_ONLY':'你右侧面颊有可见腮红，左侧尚未明确确认','APPLIED':'唇部有可见唇色','NOT_APPLIED':'目前没有明确确认到唇色','OBVIOUS_OVERFLOW':'唇部外缘有明显可见的颜色溢出'}
    lead = '现在可以确认：' if result['confidence']>=settings.confidence_high else '目前只可以初步判断：'
    return prefix+lead+states[result['status']]+'。你可以选择重拍或继续步骤。'
