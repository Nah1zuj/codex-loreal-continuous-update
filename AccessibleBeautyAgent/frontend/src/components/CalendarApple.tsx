/** Original line art inspired by the supplied apple mood boards. */
export function CalendarApple({variant=0}:{variant?:number}){
 return <svg className={'calendar-apple apple-variant-'+variant%3} viewBox="0 0 64 68" aria-hidden="true" focusable="false"><path className="apple-body" d="M32 18C13 8 5 22 7 37c2 16 13 27 25 22 12 5 23-6 25-22 2-15-6-29-25-19Z"/><path d="M32 19c-2-7 0-12 4-16m-3 12c9-13 18-7 18-7-3 9-10 9-18 7"/>{variant%3===0?<><path d="M19 29c-4 3-5 9-3 13"/><path className="apple-heart" d="M30 40c-10-8-3-15 2-9 5-6 12 1 2 9l-2 2Z"/></>:variant%3===1?<><path d="m15 35 34 0M32 22v32"/><path d="m20 45 24-21m-24 0 24 21"/></>:<><path d="M20 32c1-4 5-4 6 0m12 0c1-4 5-4 6 0M25 43q7 7 14 0"/><path d="m10 16-3-4m47 4 4-4"/></>}</svg>
}
