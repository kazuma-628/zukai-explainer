// 手描き風の線を描く。HTML要素に data-rough="種類" を付けると、その位置に描画される。
// 種類: panel / card / pill / hatch / circle / shelf / conveyor / bubble / arrow
// 共通: data-fill="#色"  bubble: data-tail="down|up|left|right"  arrow: data-dir="right|left|down|up" data-color="#色"
(function () {
  document.fonts.ready.then(function () {
    var svg = document.getElementById('ink');
    var rc = rough.svg(svg);
    var page = document.getElementById('page').getBoundingClientRect();
    var INK = '#2A2A2A';
    function R(el) { var r = el.getBoundingClientRect(); return { x: r.left - page.left, y: r.top - page.top, w: r.width, h: r.height }; }
    function add(n) { svg.appendChild(n); }
    document.querySelectorAll('[data-rough]').forEach(function (el, i) {
      var k = el.dataset.rough, b = R(el), fill = el.dataset.fill || '#FFFFFF';
      var seed = i + 1;
      if (k === 'panel') add(rc.rectangle(b.x, b.y, b.w, b.h, { fill: fill, fillStyle: 'solid', stroke: INK, strokeWidth: 3, roughness: 1.6, seed: seed }));
      if (k === 'card' || k === 'pill') add(rc.rectangle(b.x, b.y, b.w, b.h, { fill: fill, fillStyle: 'solid', stroke: INK, strokeWidth: 2.5, roughness: 1.2, seed: seed }));
      if (k === 'hatch') add(rc.rectangle(b.x, b.y, b.w, b.h, { fill: fill, fillStyle: 'hachure', hachureGap: 6, fillWeight: 2.5, stroke: INK, strokeWidth: 2.5, roughness: 1.4, seed: seed }));
      if (k === 'circle') add(rc.ellipse(b.x + b.w / 2, b.y + b.h / 2, b.w, b.h, { fill: fill, fillStyle: 'solid', stroke: INK, strokeWidth: 2.5, roughness: 1.2, seed: seed }));
      if (k === 'shelf') add(rc.line(b.x - 6, b.y + b.h, b.x + b.w + 6, b.y + b.h, { stroke: '#7A4E2D', strokeWidth: 9, roughness: 1.2, seed: seed }));
      if (k === 'conveyor') {
        add(rc.line(b.x, b.y, b.x + b.w, b.y, { stroke: '#555', strokeWidth: 6, roughness: 1, seed: seed }));
        add(rc.line(b.x, b.y + 24, b.x + b.w, b.y + 24, { stroke: '#555', strokeWidth: 6, roughness: 1, seed: seed }));
        for (var x = b.x + 20; x < b.x + b.w; x += 54) add(rc.circle(x, b.y + 12, 20, { fill: '#BBB', fillStyle: 'solid', stroke: '#555', strokeWidth: 2, roughness: 0.8, seed: seed }));
      }
      if (k === 'bubble') {
        var cx = b.x + b.w / 2, cy = b.y + b.h / 2, t = el.dataset.tail || 'down', tail;
        if (t === 'down') tail = [[cx - 16, b.y + b.h - 8], [cx - 6, b.y + b.h + 34], [cx + 18, b.y + b.h - 6]];
        if (t === 'up') tail = [[cx - 16, b.y + 8], [cx - 6, b.y - 34], [cx + 18, b.y + 6]];
        if (t === 'left') tail = [[b.x + 30, cy + b.h * 0.18], [b.x - 30, cy + b.h * 0.55], [b.x + 52, cy + b.h * 0.34]];
        if (t === 'right') tail = [[b.x + b.w - 30, cy + b.h * 0.18], [b.x + b.w + 30, cy + b.h * 0.55], [b.x + b.w - 52, cy + b.h * 0.34]];
        add(rc.polygon(tail, { fill: '#FFFFFF', fillStyle: 'solid', stroke: INK, strokeWidth: 2.5, roughness: 1, seed: seed }));
        add(rc.ellipse(cx, cy, b.w * 1.08, b.h * 1.12, { fill: '#FFFFFF', fillStyle: 'solid', stroke: INK, strokeWidth: 2.5, roughness: 1, seed: seed }));
      }
      if (k === 'arrow') {
        var d = el.dataset.dir || 'right', o = { stroke: el.dataset.color || '#E07A1F', strokeWidth: 8, roughness: 1.3, seed: seed };
        var x0, y0, x1, y1;
        if (d === 'right') { y0 = y1 = b.y + b.h / 2; x0 = b.x; x1 = b.x + b.w; }
        if (d === 'left') { y0 = y1 = b.y + b.h / 2; x0 = b.x + b.w; x1 = b.x; }
        if (d === 'down') { x0 = x1 = b.x + b.w / 2; y0 = b.y; y1 = b.y + b.h; }
        if (d === 'up') { x0 = x1 = b.x + b.w / 2; y0 = b.y + b.h; y1 = b.y; }
        var ang = Math.atan2(y1 - y0, x1 - x0), L = 28;
        add(rc.line(x0, y0, x1, y1, o));
        add(rc.line(x1, y1, x1 - L * Math.cos(ang - 0.7), y1 - L * Math.sin(ang - 0.7), o));
        add(rc.line(x1, y1, x1 - L * Math.cos(ang + 0.7), y1 - L * Math.sin(ang + 0.7), o));
      }
    });
    document.body.dataset.ready = '1';
  });
})();
