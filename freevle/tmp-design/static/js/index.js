function coverBottom() {
  var liHeight = 0;
  $('ul#quicknav > li').each(function() {
    if($(this).outerHeight() > liHeight) {
      liHeight = Math.round($(this).outerHeight());
    }
    console.log(liHeight);
  });
  if($('body').innerWidth() > 999) {
    $('#indexcover').css('margin-bottom', -1 * (liHeight + 24));
    $('ul#quicknav > li').css('min-height', liHeight);
  } else {
    $('#indexcover').css('margin-bottom', 0);
    $('ul#quicknav > li').css('min-height', 0);
  }
}

$(document).ready(function() {

  $(window).load(function() {
    coverBottom();
  });

  $(window).resize(function() {
    coverBottom();
  });

});
