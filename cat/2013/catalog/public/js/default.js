$(document).ready(function(){
        // --- language selector
        $('#t_lang_select span').click(function(){
            $('#language_select_box').show();
        })
        $('#language_select_box').mouseleave(function(){
            $(this).hide();
        });
        $('#language_select_box li').click(function(){
            var ref = $(this).find('a').attr('href');
            window.location = ref;
        });
        // ---
});

