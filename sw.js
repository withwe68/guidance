/* 꾸르실료 길잡이 — 서비스워커
 * 내용(기도문·index.html 등)을 고쳐 올릴 때마다 VERSION 숫자만 올리면
 * 사용자 휴대폰에 새 버전이 자동으로 설치됩니다.
 */
const VERSION = 'v1';
const CACHE_APP = 'gj-app-' + VERSION;      // 앱 본체(필수 파일)
const CACHE_SHEET = 'gj-sheet';             // 성가 악보 이미지(버전과 무관하게 유지)
const CACHE_FONT = 'gj-font';               // 구글 웹폰트(한 번 본 글자 조각만 저장)

// 상대경로: GitHub Pages(/저장소명/)처럼 하위 경로에 올려도 동작
const APP_FILES = [
  './',
  './index.html',
  './data/guide-data.js',
  './images/logo.png',
  './images/yeonhui-outline.png',
  './images/sheet-gwonneung.jpg',
  './images/sheet-podo.jpg',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_APP).then((c) =>
      // 한 파일이 없어도 설치가 통째로 실패하지 않도록 개별 처리
      Promise.all(APP_FILES.map((u) => c.add(u).catch(() => null)))
    )
  );
  // 새 버전을 기다리지 않고 바로 활성화 (index.html의 업데이트 안내와 함께 사용)
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k.startsWith('gj-app-') && k !== CACHE_APP)
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('message', (e) => {
  if (e.data === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // 음원(MP3)·범위요청(Range)은 캐시하지 않고 그대로 통과 (재생 오류 방지)
  if (req.headers.has('range') || /\.(mp3|m4a|wav)$/i.test(url.pathname)) return;

  // 같은 출처: 앱 본체
  if (url.origin === self.location.origin) {
    // 화면 이동(주소 입력·홈 화면 실행)은 네트워크 우선, 실패 시 캐시된 index.html
    // 전파가 약해 3.5초 안에 응답이 없으면 캐시본을 먼저 보여줌
    if (req.mode === 'navigate') {
      const timeout = new Promise((_, rej) => setTimeout(rej, 3500));
      e.respondWith(
        Promise.race([fetch(req), timeout])
          .then((res) => {
            if (res && res.ok) {
              const copy = res.clone();
              caches.open(CACHE_APP).then((c) => c.put('./index.html', copy));
            }
            return res;
          })
          .catch(() => caches.match('./index.html').then((h) => h || fetch(req)))
      );
      return;
    }
    // 그 외 파일: 캐시를 먼저 보여주고 뒤에서 갱신 (빠르고 오프라인 가능)
    e.respondWith(
      caches.match(req).then((hit) => {
        const net = fetch(req)
          .then((res) => {
            if (res && res.ok) {
              const copy = res.clone();
              caches.open(CACHE_APP).then((c) => c.put(req, copy));
            }
            return res;
          })
          .catch(() => hit);
        return hit || net;
      })
    );
    return;
  }

  // 구글 웹폰트: 캐시 우선 + 뒤에서 갱신. 못 불러오면 index.html의 대체 글꼴(맑은 고딕 등)로 표시
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(
      caches.open(CACHE_FONT).then((c) =>
        c.match(req).then((hit) => {
          const net = fetch(req)
            .then((res) => { if (res && (res.ok || res.type === 'opaque')) c.put(req, res.clone()); return res; })
            .catch(() => hit);
          return hit || net;
        })
      )
    );
    return;
  }

  // 다른 출처: 사무국 사이트의 악보 이미지만 한 번 본 것을 저장해 오프라인에서도 보이게 함
  if (url.hostname === 'imdong.or.kr' && /\.(jpg|jpeg|png)$/i.test(url.pathname)) {
    e.respondWith(
      caches.open(CACHE_SHEET).then((c) =>
        c.match(req).then((hit) =>
          hit ||
          fetch(req).then((res) => {
            c.put(req, res.clone());
            return res;
          })
        )
      )
    );
  }
  // 오늘의 미사(iframe) 등 그 밖의 외부 주소는 개입하지 않음
});
