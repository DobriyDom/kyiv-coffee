$('.Delay').each(function(i) {
   var delay = this.getAttribute('delay')
  $(this).css('opacity', 0);
  $(this).delay(delay * i).animate({
    'opacity': 1.0
  }, 1000);
});