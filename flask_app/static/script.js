$(document).ready(function() {
    $('#start-form').on('submit', function(e) {
        e.preventDefault();
        var person = $('#person').val();
        var user_id = $('#user_id').val();

        $.post('/start_conversation', { person: person, user_id: user_id }, function(data) {
            $('#responses').append('<div><strong>Assistant:</strong> ' + data.translated + '</div>');
            $('#input-form').show();
        });
    });

    $('#input-form').on('submit', function(e) {
        e.preventDefault();
        var user_input_text = $('#user_input_text').val();
        var user_id = $('#user_id').val();

        $.post('/continue_conversation', { user_input_text: user_input_text, user_id: user_id }, function(data) {
            $('#responses').append('<div><strong>You:</strong> ' + user_input_text + '</div>');
            $('#responses').append('<div><strong>Assistant:</strong> ' + data.translated + '</div>');
            $('#user_input_text').val('');

            if (data.response.toLowerCase() == "goodbye") {
                $('#input-form').hide();
            }
        });
    });
});
