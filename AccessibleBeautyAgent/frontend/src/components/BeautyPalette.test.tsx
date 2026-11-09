import { renderToStaticMarkup } from 'react-dom/server'
import { expect, it } from 'vitest'
import { BeautyPalette } from './BeautyPalette'

it('presents independent brand-neutral inspiration in a warm tone', () => {
  const html = renderToStaticMarkup(<BeautyPalette />)
  expect(html).toContain('不限定任何品牌')
  expect(html).toContain('已经拥有和熟悉的物品')
  expect(html).not.toMatch(/欧莱雅|L’Oréal|支付宝|比赛/)
})
