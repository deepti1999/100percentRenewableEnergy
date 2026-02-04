document.addEventListener("DOMContentLoaded", function() {
    const checkbox = document.querySelector("#id_is_fixed");
    const statusField = document.querySelector("#id_status_value");
    const targetField = document.querySelector("#id_target_value");
    const userInputField = document.querySelector("#id_user_input");
    const formulaField = document.querySelector("#id_formula");

    function toggleEditable() {
        if (checkbox) {
            const fixed = checkbox.checked;
            
            // Enable/disable value fields based on is_fixed
            if (statusField) {
                statusField.readOnly = !fixed;
                statusField.disabled = !fixed;
                statusField.style.backgroundColor = fixed ? '#fff' : '#e9ecef';
            }
            
            if (targetField) {
                targetField.readOnly = !fixed;
                targetField.disabled = !fixed;
                targetField.style.backgroundColor = fixed ? '#fff' : '#e9ecef';
            }
            
            if (userInputField) {
                userInputField.readOnly = !fixed;
                userInputField.disabled = !fixed;
                userInputField.style.backgroundColor = fixed ? '#fff' : '#e9ecef';
            }
            
            // Formula is always readonly
            if (formulaField) {
                formulaField.readOnly = true;
                formulaField.disabled = true;
                formulaField.style.backgroundColor = '#e9ecef';
            }
        }
    }

    if (checkbox) {
        checkbox.addEventListener("change", toggleEditable);
        toggleEditable(); // run once on page load
    }
});
