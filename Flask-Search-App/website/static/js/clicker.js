$('.clicker-content').hide();

$('.clicker').click(function(){
    $(this).nextUntil('.clicker').slideToggle('normal');
  });

document.getElementById('demo').innerHTML = "This is changed by js file"