import { readFile } from 'fs/promises';
import path from 'path';

import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

function injectThemeAssets(html: string) {
  const marker = 'data-formata-theme-assets="1"';
  if (html.includes(marker)) return html;

  const injection = `<link ${marker} rel="stylesheet" href="/ydata-profile-theme.css"><script ${marker}>(function(){function a(){try{var e=window.parent&&window.parent.document&&window.parent.document.documentElement;if(!e)return!1;var t=e.classList&&e.classList.contains('dark');document.documentElement.dataset.theme=t?'dark':'light';try{var r=new MutationObserver(function(){a()});r.observe(e,{attributes:!0,attributeFilter:['class']})}catch(n){}return!0}catch(n){return!1}}function i(){try{var e=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)');document.documentElement.dataset.theme=e&&e.matches?'dark':'light';if(e&&e.addEventListener)e.addEventListener('change',i)}catch(t){}}if(!a())i()})();</script>`;

  const styleCloseIndex = html.toLowerCase().indexOf('</style>');
  if (styleCloseIndex !== -1) {
    const insertAt = styleCloseIndex + '</style>'.length;
    return `${html.slice(0, insertAt)}${injection}${html.slice(insertAt)}`;
  }

  const bodyIndex = html.toLowerCase().indexOf('<body');
  if (bodyIndex !== -1) {
    return `${html.slice(0, bodyIndex)}${injection}${html.slice(bodyIndex)}`;
  }

  return `${injection}${html}`;
}

export async function GET(_request: Request, { params }: { params: { jobId: string } }) {
  const filePath = path.join(process.cwd(), `${params.jobId}_clean_profile.html`);
  const fallbackPath = path.join(process.cwd(), 'cf61c556-961f-484d-9110-d25b651ecf67_clean_profile.html');

  try {
    const html = await readFile(filePath, 'utf8');
    return new NextResponse(injectThemeAssets(html), {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      },
    });
  } catch {
    try {
      const html = await readFile(fallbackPath, 'utf8');
      return new NextResponse(injectThemeAssets(html), {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'no-store',
        },
      });
    } catch {
      return new NextResponse('Report not found', { status: 404 });
    }
  }
}
