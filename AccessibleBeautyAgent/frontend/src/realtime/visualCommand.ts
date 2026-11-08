/** Intent never grants camera or analysis permission. */
export function isVisualRequest(message:string){return !/(不要|不用|不想|don't|do not)/i.test(message)&&/(帮我看看|帮我检查|现在呢|调整好了.*(看看|检查|再看)|重新检查|再检查一次|再看一次|检查腮红|检查唇|左右是不是一样|check again|check my (blush|lips)|check this)/i.test(message)}
