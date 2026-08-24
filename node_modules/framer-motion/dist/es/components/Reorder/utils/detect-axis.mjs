const isSeparated = (a, b) => a.max <= b.min || b.max <= a.min;
function detectAxis(layouts) {
    let x = false;
    let y = false;
    for (let i = 0; i < layouts.length; i++) {
        for (let j = i + 1; j < layouts.length; j++) {
            x || (x = isSeparated(layouts[i].x, layouts[j].x));
            y || (y = isSeparated(layouts[i].y, layouts[j].y));
            if (x && y)
                return "xy";
        }
    }
    return x ? "x" : "y";
}

export { detectAxis };
//# sourceMappingURL=detect-axis.mjs.map
