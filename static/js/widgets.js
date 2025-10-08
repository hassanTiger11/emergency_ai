/**
 * Widget Generation Module
 * Generates interactive widget components for report data
 */

// This file contains the widget generation functions
// Full implementation extracted from index.html (lines 2186-2369)

function generateWidgets(analysis) {
    let widgetsHtml = '<div class="widgets-container">';

    // Patient Information Widget
    if (analysis.patient) {
        widgetsHtml += `
            <div class="widget-section">
                <h3>👤 Patient Information</h3>
                <div class="widget-grid">
                    <div class="widget-item">
                        <span class="widget-label">Name:</span>
                        <span class="widget-value">${analysis.patient.name || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Age:</span>
                        <span class="widget-value">${analysis.patient.age || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Gender:</span>
                        <span class="widget-value">${analysis.patient.gender || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Nationality:</span>
                        <span class="widget-value">${analysis.patient.nationality || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">ID:</span>
                        <span class="widget-value">${analysis.patient.ID || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Scene Information Widget
    if (analysis.scene) {
        widgetsHtml += `
            <div class="widget-section">
                <h3>📍 Scene Information</h3>
                <div class="widget-grid">
                    <div class="widget-item">
                        <span class="widget-label">Date:</span>
                        <span class="widget-value">${analysis.scene.date || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Time:</span>
                        <span class="widget-value">${analysis.scene.time || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Caller Phone:</span>
                        <span class="widget-value">${analysis.scene.caller_phone || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Location:</span>
                        <span class="widget-value">${analysis.scene.location || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Case Category:</span>
                        <span class="widget-value">${analysis.scene.case_category || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Chief Complaint:</span>
                        <span class="widget-value">${analysis.scene.chief_complaint || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // History Widget
    if (analysis.history) {
        widgetsHtml += `
            <div class="widget-section history-widget">
                <h3>📋 History</h3>
                <div class="widget-grid">
                    <div class="widget-item">
                        <span class="widget-label">Onset:</span>
                        <span class="widget-value">${analysis.history.onset || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Duration:</span>
                        <span class="widget-value">${analysis.history.duration || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Allergies:</span>
                        <span class="widget-value">${analysis.history.allergies || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Medications:</span>
                        <span class="widget-value">${analysis.history.medications || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Past History:</span>
                        <span class="widget-value">${analysis.history.past_history || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Vital Signs Widget
    if (analysis.vitals) {
        widgetsHtml += `
            <div class="widget-section vitals-widget">
                <h3>💓 Vital Signs</h3>
                <div class="widget-grid">
                    <div class="widget-item">
                        <span class="widget-label">Blood Pressure:</span>
                        <span class="widget-value">${analysis.vitals.bp_systolic && analysis.vitals.bp_diastolic ? `${analysis.vitals.bp_systolic}/${analysis.vitals.bp_diastolic}` : 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Heart Rate:</span>
                        <span class="widget-value">${analysis.vitals.hr || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Respiratory Rate:</span>
                        <span class="widget-value">${analysis.vitals.rr || 'N/A'}</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">SpO2:</span>
                        <span class="widget-value">${analysis.vitals.spo2 || 'N/A'}%</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">Temperature:</span>
                        <span class="widget-value">${analysis.vitals.temp || 'N/A'}°C</span>
                    </div>
                    <div class="widget-item">
                        <span class="widget-label">GCS:</span>
                        <span class="widget-value">${analysis.vitals.gcs || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Interventions Widget
    if (analysis.interventions && analysis.interventions.length > 0) {
        widgetsHtml += `
            <div class="widget-section interventions-widget">
                <h3>⚕️ Interventions</h3>
                <div class="interventions-list">
                    ${analysis.interventions.map(intervention => `
                        <div class="intervention-item">${intervention}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Severity Widget
    widgetsHtml += `
        <div class="widget-section severity-widget">
            <h3>🚨 Assessment</h3>
            <div class="widget-grid">
                <div class="widget-item">
                    <span class="widget-label">Severity:</span>
                    <span class="widget-value highlight">${analysis.severity || 'N/A'}</span>
                </div>
                <div class="widget-item">
                    <span class="widget-label">Recommendation:</span>
                    <span class="widget-value">${analysis.recommendation || 'N/A'}</span>
                </div>
            </div>
        </div>
    `;

    widgetsHtml += '</div>'; // Close widgets-container
    return widgetsHtml;
}

