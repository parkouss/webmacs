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
    textzoom.totalRatio = 1;
    textzoom.changeFont(0);
    return textzoom.totalRatio;
}


textzoom.changeFont = function(ratioDiff) {
    var call, changeFontSizeCalls, el, i, j, len, len1, multiplier, prevRatio, relevantElements, results;
    changeFontSizeCalls = [];
    prevRatio = textzoom.totalRatio;
    textzoom.totalRatio += ratioDiff;
    textzoom.totalRatio = Math.round(textzoom.totalRatio * 10) / 10;
    multiplier = textzoom.totalRatio / prevRatio;
    relevantElements = document.querySelectorAll('body, body *');

    if (textzoom.totalRatio === 1) {
	for (i = 0, len = relevantElements.length; i < len; i++) {
	    el = relevantElements[i];
	    el.style['transition'] = null;
	    el.style['font-size'] = null;
	    el.style['line-height'] = null;
	}
    }
    [].forEach.call(relevantElements, function(el) {
	var computedStyle, currentLh, fontSize, lineHeight, tagName;
	tagName = el.tagName;
	if (tagName.match(textzoom.IGNORED_TAGS)) {
	    return;
	}
	computedStyle = getComputedStyle(el);
	if (!textzoom.isBlank(el.innerText) || (tagName === 'TEXTAREA')) {
	    currentLh = computedStyle.lineHeight;
	    if (currentLh.indexOf('px') !== -1) {
		lineHeight = textzoom.multiplyByRatio(currentLh, multiplier);
	    }
	}
	fontSize = textzoom.multiplyByRatio(computedStyle.fontSize, multiplier);
	return changeFontSizeCalls.push(function() {
	    el.style['transition'] = 'font 0s';
	    textzoom.addImportantStyle(el, 'font-size', fontSize);
	    if (lineHeight !== void 0) {
		return textzoom.addImportantStyle(el, 'line-height', lineHeight);
	    }
	});
    });

    for (j = 0, len1 = changeFontSizeCalls.length; j < len1; j++) {
	call = changeFontSizeCalls[j];
	call();
    }
    return textzoom.totalRatio;
};
