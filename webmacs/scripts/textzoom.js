var textzoom = {};

textzoom.totalRatio = 1;

textzoom.IGNORED_TAGS = /SCRIPT|NOSCRIPT|LINK|BR|EMBED|IFRAME|IMG|VIDEO|CANVAS|STYLE/;

textzoom.multiplyByRatio = function(value, multiplier) {
  return (parseFloat(value) * multiplier) + 'px';
};

textzoom.addImportantStyle = function(el, name, value) {
  return el.style.cssText += name + ": " + value + " !important;";
};

textzoom.isBlank = function(str) {
    return !str || /^\s*$/.test(str)
}

textzoom.resetChangeFont = function() {
    for (let i=0; i<window.frames.length; i++) {
        post_message(window.frames[i], "textzoom.resetChangeFont");
    }
    textzoom.totalRatio = 1;
    textzoom.changeFont(0, true);
    return textzoom.totalRatio;
}


textzoom.changeFont = function(ratioDiff, prevent) {
    let prevRatio = textzoom.totalRatio;
    textzoom.totalRatio += ratioDiff;
    textzoom.totalRatio = Math.round(textzoom.totalRatio * 10) / 10;
    let multiplier = textzoom.totalRatio / prevRatio;
    let relevantElements = document.querySelectorAll('body, body *');

    if (!prevent) {
        for (let i=0; i<window.frames.length; i++) {
            post_message(window.frames[i], "textzoom.changeFont", ratioDiff);
        }
    }

    if (textzoom.totalRatio === 1) {
	      for (let el of relevantElements) {
	          el.style['transition'] = null;
	          el.style['font-size'] = null;
	          el.style['line-height'] = null;
	      }
    }
    for (let el of relevantElements) {
	      if (el.tagName.match(textzoom.IGNORED_TAGS)) {
	          continue;
	      }
        let lineHeight = null;
	      let computedStyle = getComputedStyle(el);
	      if (!textzoom.isBlank(el.innerText) || (el.tagName === 'TEXTAREA')) {
	          if (computedStyle.lineHeight.indexOf('px') !== -1) {
		            lineHeight = textzoom.multiplyByRatio(computedStyle.lineHeight,
                                                      multiplier);
	          }
	      }
	      let fontSize = textzoom.multiplyByRatio(computedStyle.fontSize, multiplier);

	      el.style['transition'] = 'font 0s';
	      textzoom.addImportantStyle(el, 'font-size', fontSize);
	      if (lineHeight !== null) {
		        textzoom.addImportantStyle(el, 'line-height', lineHeight);
	      }
    }
    return textzoom.totalRatio;
}


if (self !== top) {
    register_message_handler("textzoom.changeFont", textzoom.changeFont);
    register_message_handler("textzoom.resetChangeFont",
                             textzoom.resetChangeFont);
}
