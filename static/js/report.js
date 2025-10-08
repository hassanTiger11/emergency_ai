/**
 * Report Display Module
 * Handles report generation and display
 * Note: This file includes generateProfessionalReport extracted from index.html
 */

function displayReport(data) {
    originalAnalysis = data.analysis;
    
    // Show report section
    const reportSection = document.getElementById('reportSection');
    reportSection.style.display = 'block';
    
    // Generate widgets
    const widgetsHtml = generateWidgets(data.analysis);
    
    // Generate professional report
    const professionalReportHtml = `
        <div class="professional-report-section">
            <div class="section-header">DETAILED MEDICAL REPORT</div>
            ${generateProfessionalReport(data.analysis)}
        </div>
    `;
    
    // Action buttons
    const actionsHtml = `
        <div class="action-buttons">
            <button class="btn btn-primary" onclick="toggleEditMode()">Edit Report</button>
            <button class="btn btn-primary" onclick="generatePDFReport()">📄 Download PDF Report</button>
        </div>
    `;
    
    // Transcript section
    let transcriptHtml = '';
    if (data.transcript) {
        transcriptHtml = `
            <div class="transcript-section">
                <h3>📝 Audio Transcript</h3>
                <p>${data.transcript}</p>
            </div>
        `;
    }
    
    // Combine all sections
    reportSection.innerHTML = widgetsHtml + professionalReportHtml + actionsHtml + transcriptHtml;
}

// Professional report generation function
// NOTE: This is a simplified version. For the full implementation,
// refer to the original index.html lines 2370-2765
function generateProfessionalReport(analysis) {
    let reportHtml = '<div class="professional-report">';
    
    // Report Header
    reportHtml += `
        <div class="report-header-section">
            <div class="report-title">PARAMEDIC PATIENT CARE REPORT</div>
            <div class="report-subtitle">Makkah Emergency Medical Services</div>
            <div class="report-meta">
                <div class="report-info-row">
                    <span class="report-label">Date:</span>
                    <span class="report-value editable-field" data-field="scene.date">${analysis.scene?.date || new Date().toISOString().split('T')[0]}</span>
                </div>
                <div class="report-info-row">
                    <span class="report-label">Time:</span>
                    <span class="report-value editable-field" data-field="scene.time">${analysis.scene?.time || new Date().toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit'})}</span>
                </div>
            </div>
        </div>
    `;

    // Patient Demographics
    if (analysis.patient) {
        reportHtml += `
            <div class="report-section">
                <div class="section-header">PATIENT DEMOGRAPHICS</div>
                <div class="section-content">
                    <div class="demographics-grid">
                        <div class="demo-item">
                            <span class="demo-label">Name:</span>
                            <span class="demo-value editable-field" data-field="patient.name">${analysis.patient.name || 'Unknown'}</span>
                        </div>
                        <div class="demo-item">
                            <span class="demo-label">Age:</span>
                            <span class="demo-value editable-field" data-field="patient.age">${analysis.patient.age || 'Unknown'}</span>
                        </div>
                        <div class="demo-item">
                            <span class="demo-label">Gender:</span>
                            <span class="demo-value editable-field" data-field="patient.gender">${analysis.patient.gender || 'Unknown'}</span>
                        </div>
                        <div class="demo-item">
                            <span class="demo-label">Nationality:</span>
                            <span class="demo-value editable-field" data-field="patient.nationality">${analysis.patient.nationality || 'Unknown'}</span>
                        </div>
                        <div class="demo-item">
                            <span class="demo-label">ID:</span>
                            <span class="demo-value editable-field" data-field="patient.ID">${analysis.patient.ID || 'Unknown'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Scene Information
    if (analysis.scene) {
        reportHtml += `
            <div class="report-section">
                <div class="section-header">SCENE INFORMATION</div>
                <div class="section-content">
                    <div class="scene-grid">
                        <div class="scene-item">
                            <span class="scene-label">Location:</span>
                            <span class="scene-value editable-field" data-field="scene.location">${analysis.scene.location || 'Unknown'}</span>
                        </div>
                        <div class="scene-item">
                            <span class="scene-label">Caller Phone:</span>
                            <span class="scene-value editable-field" data-field="scene.caller_phone">${analysis.scene.caller_phone || 'Unknown'}</span>
                        </div>
                        <div class="scene-item">
                            <span class="scene-label">Case Category:</span>
                            <span class="scene-value editable-field" data-field="scene.case_category">${analysis.scene.case_category || 'Unknown'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Chief Complaint
    reportHtml += `
        <div class="report-section">
            <div class="section-header">CHIEF COMPLAINT</div>
            <div class="section-content">
                <div class="chief-complaint-box">
                    <div class="complaint-text editable-field" data-field="chief_complaint">${analysis.chief_complaint || analysis.scene?.chief_complaint || 'Not provided'}</div>
                </div>
            </div>
        </div>
    `;

    // Vital Signs
    if (analysis.vitals) {
        reportHtml += `
            <div class="report-section">
                <div class="section-header">VITAL SIGNS</div>
                <div class="section-content">
                    <div class="vitals-table">
                        <div class="vital-row">
                            <div class="vital-cell">
                                <span class="vital-label">Blood Pressure:</span>
                                <span class="vital-value editable-field" data-field="vitals.bp">${analysis.vitals?.bp_systolic && analysis.vitals?.bp_diastolic ? `${analysis.vitals.bp_systolic}/${analysis.vitals.bp_diastolic}` : '___/___'}</span>
                            </div>
                            <div class="vital-cell">
                                <span class="vital-label">Heart Rate:</span>
                                <span class="vital-value editable-field" data-field="vitals.hr">${analysis.vitals?.hr || '___'}</span>
                            </div>
                            <div class="vital-cell">
                                <span class="vital-label">Respiratory Rate:</span>
                                <span class="vital-value editable-field" data-field="vitals.rr">${analysis.vitals?.rr || '___'}</span>
                            </div>
                        </div>
                        <div class="vital-row">
                            <div class="vital-cell">
                                <span class="vital-label">SpO2:</span>
                                <span class="vital-value editable-field" data-field="vitals.spo2">${analysis.vitals?.spo2 || '___'}%</span>
                            </div>
                            <div class="vital-cell">
                                <span class="vital-label">Temperature:</span>
                                <span class="vital-value editable-field" data-field="vitals.temp">${analysis.vitals?.temp || '___'}°C</span>
                            </div>
                            <div class="vital-cell">
                                <span class="vital-label">GCS:</span>
                                <span class="vital-value editable-field" data-field="vitals.gcs">${analysis.vitals?.gcs || '___'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Assessment
    reportHtml += `
        <div class="report-section">
            <div class="section-header">ASSESSMENT & PLAN</div>
            <div class="section-content">
                <div class="assessment-grid">
                    <div class="assessment-item">
                        <span class="assessment-label">Clinical Assessment:</span>
                        <span class="assessment-value editable-field" data-field="reasoning">${analysis.reasoning || 'Assessment pending'}</span>
                    </div>
                    <div class="assessment-item">
                        <span class="assessment-label">Recommendation:</span>
                        <span class="assessment-value editable-field" data-field="recommendation">${analysis.recommendation || 'Recommendation pending'}</span>
                    </div>
                    <div class="assessment-item">
                        <span class="assessment-label">Severity:</span>
                        <span class="assessment-value editable-field" data-field="severity">${analysis.severity || 'Unknown'}</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Signature Section
    reportHtml += `
        <div class="report-section signature-section">
            <div class="section-header">SIGNATURES</div>
            <div class="section-content">
                <div class="signature-grid">
                    <div class="signature-item">
                        <span class="signature-label">Paramedic/EMT:</span>
                        <span class="signature-value editable-field" data-field="signatures.paramedic">_________________________</span>
                    </div>
                    <div class="signature-item">
                        <span class="signature-label">Time:</span>
                        <span class="signature-value editable-field" data-field="signatures.time">_________________________</span>
                    </div>
                    <div class="signature-item">
                        <span class="signature-label">Receiving Hospital:</span>
                        <span class="signature-value editable-field" data-field="signatures.hospital">_________________________</span>
                    </div>
                    <div class="signature-item">
                        <span class="signature-label">Receiving Staff:</span>
                        <span class="signature-value editable-field" data-field="signatures.staff">_________________________</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    reportHtml += '</div>'; // Close professional-report
    return reportHtml;
}

// PDF Generation Function
async function generatePDFReport() {
    try {
        if (!originalAnalysis) {
            alert('No report data available. Please generate a report first.');
            return;
        }

        // Show loading state
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = '⏳ Generating PDF...';
        button.disabled = true;

        // Prepare data for PDF generation
        const pdfData = {
            session_id: SESSION_ID,
            analysis: originalAnalysis
        };

        console.log('📄 Generating PDF report...');

        // Call the PDF generation endpoint
        const response = await fetch('/api/generate-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(pdfData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate PDF');
        }

        // Get the PDF blob
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Get filename from response headers or create default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'medical_report.pdf';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        
        // Trigger download
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log('✅ PDF report downloaded successfully');

    } catch (error) {
        console.error('❌ Error generating PDF:', error);
        alert('Failed to generate PDF report: ' + error.message);
    } finally {
        // Reset button state
        const button = event.target;
        button.textContent = '📄 Download PDF Report';
        button.disabled = false;
    }
}

