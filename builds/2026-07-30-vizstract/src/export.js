/* Vizstract — client-side export: SVG string -> downloadable .svg,
   and SVG -> Canvas -> downloadable .png. No server, no external service. */
(function () {
  "use strict";
  window.Vizstract = window.Vizstract || {};

  function triggerDownload(href, filename) {
    var a = document.createElement("a");
    a.href = href;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function downloadSVG(svgString, filename) {
    var blob = new Blob([svgString], { type: "image/svg+xml" });
    var url = URL.createObjectURL(blob);
    triggerDownload(url, filename);
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1000);
  }

  function svgToPngDataUrl(svgString, width, height) {
    return new Promise(function (resolve, reject) {
      var svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
      var url = URL.createObjectURL(svgBlob);
      var img = new Image();
      img.onload = function () {
        var canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        var ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);
        URL.revokeObjectURL(url);
        resolve(canvas.toDataURL("image/png"));
      };
      img.onerror = function (e) {
        URL.revokeObjectURL(url);
        reject(e);
      };
      img.src = url;
    });
  }

  function downloadPNG(svgString, width, height, filename) {
    return svgToPngDataUrl(svgString, width, height).then(function (dataUrl) {
      triggerDownload(dataUrl, filename);
      return dataUrl;
    });
  }

  window.Vizstract.Export = {
    downloadSVG: downloadSVG,
    downloadPNG: downloadPNG,
    svgToPngDataUrl: svgToPngDataUrl
  };
})();
