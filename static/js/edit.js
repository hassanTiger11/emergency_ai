/**
 * Edit Mode Management Module
 * Handles report editing, validation, and saving
 */

// Edit mode state
let isEditMode = false;
let originalAnalysis = null;
let editedAnalysis = null;

function toggleEditMode() {
    if (!isEditMode) {
        enterEditMode();
    } else {
        exitEditMode();
    }
}

function enterEditMode() {
    isEditMode = true;
    editedAnalysis = JSON.parse(JSON.stringify(originalAnalysis)); // Deep copy
    
    // Update UI for both widgets and professional report
    const widgetsContainer = document.querySelector('.widgets-container');
    const professionalReport = document.querySelector('.professional-report');
    
    if (widgetsContainer) {
        widgetsContainer.classList.add('edit-mode');
    }
    if (professionalReport) {
        professionalReport.classList.add('edit-mode');
    }
    
    makeWidgetsEditable();
    showEditControls();
}

function exitEditMode() {
    isEditMode = false;
    editedAnalysis = null;
    
    // Update UI for both widgets and professional report
    const widgetsContainer = document.querySelector('.widgets-container');
    const professionalReport = document.querySelector('.professional-report');
    
    if (widgetsContainer) {
        widgetsContainer.classList.remove('edit-mode');
    }
    if (professionalReport) {
        professionalReport.classList.remove('edit-mode');
    }
    
    makeWidgetsReadOnly();
    hideEditControls();
}

function makeWidgetsEditable() {
    // Handle widget values
    const widgetValues = document.querySelectorAll('.widget-value');
    widgetValues.forEach(element => {
        if (element.textContent && element.textContent !== 'N/A') {
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'widget-value editable';
            input.value = element.textContent;
            input.dataset.originalValue = element.textContent;
            addValidation(input, element);
            element.parentNode.replaceChild(input, element);
        }
    });

    // Handle professional report fields
    const editableFields = document.querySelectorAll('.editable-field');
    editableFields.forEach(element => {
        if (element.textContent && element.textContent !== 'N/A' && element.textContent !== 'Not provided' && element.textContent !== 'Not specified') {
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'editable-field editable';
            input.value = element.textContent;
            input.dataset.originalValue = element.textContent;
            input.dataset.field = element.dataset.field;
            addValidation(input, element);
            element.parentNode.replaceChild(input, element);
        }
    });
}

function makeWidgetsReadOnly() {
    // Handle widget values
    const editableWidgetInputs = document.querySelectorAll('.widget-value.editable');
    editableWidgetInputs.forEach(input => {
        const span = document.createElement('span');
        span.className = 'widget-value';
        span.textContent = input.value;
        input.parentNode.replaceChild(span, input);
    });

    // Handle professional report fields
    const editableInputs = document.querySelectorAll('.editable-field.editable');
    editableInputs.forEach(input => {
        const span = document.createElement('span');
        span.className = 'editable-field';
        span.textContent = input.value;
        span.dataset.field = input.dataset.field;
        input.parentNode.replaceChild(span, input);
    });
}

function addValidation(input, originalElement) {
    const fieldPath = input.dataset.field || '';
    const label = originalElement.parentNode.querySelector('.widget-label, .info-label, .history-label, .vital-label, .assessment-label')?.textContent.toLowerCase() || '';
    
    input.addEventListener('blur', () => validateField(input));
}

function validateField(input) {
    const value = input.value.trim();
    const fieldPath = input.dataset.field || '';
    const label = input.closest('.widget-item, .info-item, .history-item, .vital-item, .assessment-item, .demo-item, .scene-item, .medical-item, .exam-item, .treatment-item, .signature-item')?.querySelector('.widget-label, .info-label, .history-label, .vital-label, .assessment-label, .demo-label, .scene-label, .medical-label, .exam-label, .treatment-label, .signature-label')?.textContent.toLowerCase() || '';
    
    input.classList.remove('invalid');
    hideValidationMessage(input);
    
    if (!value) return true;
    
    // Validation logic
    if (fieldPath.includes('vitals.hr') || label.includes('heart rate')) {
        if (isNaN(value) || value < 0 || value > 300) {
            input.classList.add('invalid');
            showValidationMessage(input, 'Heart rate must be between 0-300 bpm');
            return false;
        }
    } else if (fieldPath.includes('vitals.bp') || label.includes('blood pressure')) {
        if (!value.match(/^\d+\/\d+$/)) {
            input.classList.add('invalid');
            showValidationMessage(input, 'Blood pressure format: systolic/diastolic (e.g., 120/80)');
            return false;
        }
    }
    
    return true;
}

function showValidationMessage(input, message) {
    let messageEl = input.parentNode.querySelector('.validation-message');
    if (!messageEl) {
        messageEl = document.createElement('div');
        messageEl.className = 'validation-message';
        input.parentNode.appendChild(messageEl);
    }
    messageEl.textContent = message;
    messageEl.classList.add('show');
}

function hideValidationMessage(input) {
    const messageEl = input.parentNode.querySelector('.validation-message');
    if (messageEl) {
        messageEl.classList.remove('show');
    }
}

function showEditControls() {
    const professionalReportSection = document.querySelector('.professional-report-section');
    if (professionalReportSection && !document.querySelector('.edit-mode-controls')) {
        const editControls = document.createElement('div');
        editControls.className = 'edit-mode-controls';
        editControls.innerHTML = `
            <div class="edit-mode-indicator">✏️ Edit Mode Active</div>
            <div class="edit-controls">
                <button class="btn-edit btn-save" onclick="saveChanges()">💾 Save Changes</button>
                <button class="btn-edit btn-cancel" onclick="cancelChanges()">❌ Cancel</button>
            </div>
        `;
        professionalReportSection.insertAdjacentElement('afterend', editControls);
    }
}

function hideEditControls() {
    const editControls = document.querySelector('.edit-mode-controls');
    if (editControls) {
        editControls.remove();
    }
}

function saveChanges() {
    const editableInputs = document.querySelectorAll('.editable-field.editable, .widget-value.editable');
    let allValid = true;
    
    editableInputs.forEach(input => {
        if (!validateField(input)) {
            allValid = false;
        }
    });
    
    if (!allValid) {
        alert('Please fix validation errors before saving.');
        return;
    }
    
    console.log('✅ Changes saved');
    exitEditMode();
}

function cancelChanges() {
    editedAnalysis = null;
    exitEditMode();
    displayReport(originalAnalysis);
}

