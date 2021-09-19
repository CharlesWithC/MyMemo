// Javascript's Sleep
function sleep(time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}

// A function to generate random color
function getRndColor(min, max) {
    var r = min + (max - min) * Math.random() | 0,
        g = min + (max - min) * Math.random() | 0,
        b = min + (max - min) * Math.random() | 0;
    return 'rgb(' + r + ',' + g + ',' + b + ')';
}

// The canvas type for round rectangle
CanvasRenderingContext2D.prototype.roundRect = function (x, y, width, height, radius = 40) {
    if (width < 2 * radius) radius = width / 2;
    if (height < 2 * radius) radius = height / 2;
    this.beginPath();
    this.moveTo(x + radius, y);
    this.arcTo(x + width, y, x + width, y + height, radius);
    this.arcTo(x + width, y + height, x, y + height, radius);
    this.arcTo(x, y + height, x, y, radius);
    this.arcTo(x, y, x + width, y, radius);
    this.closePath();
    this.fill();
    return this;
}