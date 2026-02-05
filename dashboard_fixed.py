# The issue in your code is that st.markdown() is showing HTML as code instead of rendering it.
# This happens when there are syntax errors in the HTML or missing unsafe_allow_html=True

# FIXES NEEDED:

# 1. In the AI Panel section (around line 570), the HTML has formatting issues
# Replace the entire AI panel section with this:

st.markdown("""
<div class="ai-panel">
    <div class="ai-panel-header">
        <div class="ai-icon">🤖</div>
        <h3>AI-Powered Operational Intelligence: Priority Action Queue</h3>
    </div>
    
    <div class="ai-action-item">
        <div class="action-priority p1">P1</div>
        <div class="action-content">
            <h4>Correct Temperature Zone Violations Immediately</h4>
            <p>490 SKUs currently stored in incompatible temperature zones. This is a HARD CONSTRAINT violation causing simulation failures and spoilage risk.</p>
            <div class="action-meta">
                <span>⏱️ Impact: Immediate</span>
                <span>📊 Severity: Critical</span>
                <span>🎯 ROI: Compliance + Loss Prevention</span>
            </div>
        </div>
    </div>
    
    <div class="ai-action-item">
        <div class="action-priority p1">P2</div>
        <div class="action-content">
            <h4>Relocate High-Velocity SKUs from Aisle B</h4>
            <p>35 high-velocity SKUs causing systematic gridlock at 19:00 peak hour. Forklift access blocked when &gt;2 pickers present.</p>
            <div class="action-meta">
                <span>⏱️ Impact: 24-48 hours</span>
                <span>📊 Severity: High</span>
                <span>🎯 ROI: 40% pick time reduction</span>
            </div>
        </div>
    </div>
    
    <div class="ai-action-item">
        <div class="action-priority p2">P3</div>
        <div class="action-content">
            <h4>Enforce Picker Routing Compliance Protocol</h4>
            <p>1,551 unsafe shortcuts detected (0.77% violation rate). Indicates layout inefficiency forcing unsafe behavior to meet targets.</p>
            <div class="action-meta">
                <span>⏱️ Impact: Ongoing</span>
                <span>📊 Severity: Medium</span>
                <span>🎯 ROI: Safety + Compliance</span>
            </div>
        </div>
    </div>
    
    <p style="font-size: 12px; color: var(--text-muted); margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-subtle);">
        <strong>Execution Timeline:</strong> Complete slotting optimization before Week 91 operations commence
    </p>
</div>
""", unsafe_allow_html=True)

# 2. For the Executive Summary section, escape special characters properly
# Replace f-strings in HTML with proper escaping

# 3. For better heatmap, use this configuration:
fig_heatmap = px.density_heatmap(
    heatmap_data, 
    x='hour', 
    y='aisle', 
    z='pick_count', 
    nbinsx=24,
    nbinsy=len(heatmap_data['aisle'].unique()),
    color_continuous_scale='Turbo',  # More vibrant than Viridis
    labels={'hour': 'Hour of Day (0-23)', 'aisle': 'Warehouse Aisle', 'pick_count': 'Picks'}
)

# 4. Add this CSS for better mobile responsiveness:
"""
@media (max-width: 1200px) {
    .metric-card .metric-value { font-size: 24px; }
}

@media (max-width: 992px) {
    .command-header h1 { font-size: 20px !important; }
    .ai-panel { padding: 16px; }
}

@media (max-width: 576px) {
    .metric-card { padding: 12px; }
    .ai-action-item { flex-direction: column; }
}
"""
