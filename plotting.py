import numpy as np
import plotly.graph_objects as go

# Common rest-frame emission lines (wavelength in Angstroms)
REST_FRAME_LINES = [
    # Hydrogen Lyman / Balmer series
    {"name": "Lyα", "rest_wave": 1215.67, "type": "emission", "color": "#2ca02c"},
    {"name": "Hδ", "rest_wave": 4101.74, "type": "balmer", "color": "#1f77b4"},
    {"name": "Hγ", "rest_wave": 4340.47, "type": "balmer", "color": "#1f77b4"},
    {"name": "Hβ", "rest_wave": 4861.33, "type": "balmer", "color": "#1f77b4"},
    {"name": "Hα", "rest_wave": 6562.82, "type": "balmer", "color": "#d62728"},
    # Nebular emission lines (AGN / Star-forming)
    {"name": "[O II]", "rest_wave": 3727.09, "type": "forbidden", "color": "#9467bd"},
    {"name": "[O III] 4959", "rest_wave": 4958.91, "type": "forbidden", "color": "#8c564b"},
    {"name": "[O III] 5007", "rest_wave": 5006.84, "type": "forbidden", "color": "#8c564b"},
    {"name": "[O I] 6300", "rest_wave": 6300.30, "type": "forbidden", "color": "#e377c2"},
    {"name": "[N II] 6583", "rest_wave": 6583.45, "type": "forbidden", "color": "#bcbd22"},
    {"name": "[S II] 6716", "rest_wave": 6716.44, "type": "forbidden", "color": "#17becf"},
    {"name": "[S II] 6731", "rest_wave": 6730.82, "type": "forbidden", "color": "#17becf"},
    # UV / Quasar lines
    {"name": "C IV", "rest_wave": 1549.06, "type": "uv", "color": "#ff7f0e"},
    {"name": "C III]", "rest_wave": 1908.73, "type": "uv", "color": "#ff7f0e"},
    {"name": "Mg II", "rest_wave": 2798.75, "type": "uv", "color": "#e377c2"},
    {"name": "He II", "rest_wave": 4685.70, "type": "emission", "color": "#2ca02c"},
    # Stellar absorption features
    {"name": "Ca II K", "rest_wave": 3933.66, "type": "absorption", "color": "#7f7f7f"},
    {"name": "Ca II H", "rest_wave": 3968.47, "type": "absorption", "color": "#7f7f7f"},
    {"name": "G-band", "rest_wave": 4304.40, "type": "absorption", "color": "#7f7f7f"},
    {"name": "Mg I b", "rest_wave": 5175.40, "type": "absorption", "color": "#7f7f7f"},
    {"name": "Na I D", "rest_wave": 5892.94, "type": "absorption", "color": "#7f7f7f"},
]


def create_spectrum_figure(
    obs: dict,
    object_key: str,
    dataset_source: str,
    obs_index: int = 0,
    total_obs: int = 1,
    show_line_markers: bool = True,
) -> go.Figure:
    """
    Generate an interactive, responsive Plotly figure for an astronomical spectrum.
    Uses the standard Plotly theme with larger dimensions and clear, readable font sizes.
    """
    fig = go.Figure()

    if not obs or len(obs.get("lambda", [])) == 0:
        fig.add_annotation(
            text="No spectral data available for this object",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(
            template="plotly",
            height=380,
            margin=dict(l=55, r=25, t=40, b=45),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
        )
        return fig

    wavelength = np.array(obs["lambda"])
    flux = np.array(obs["flux"])
    mask = np.array(obs.get("mask", []))

    # Filter out invalid wavelengths (<= 0)
    valid_indices = wavelength > 0

    # Filter out masked pixels if mask is provided
    if len(mask) == len(wavelength):
        if mask.dtype == bool:
            valid_indices &= ~mask
        else:
            valid_indices &= mask == 0

    w_clean = wavelength[valid_indices]
    f_clean = flux[valid_indices]

    if len(w_clean) == 0:
        w_clean = wavelength
        f_clean = flux

    # Trace: High-contrast spectral flux line
    fig.add_trace(
        go.Scatter(
            x=w_clean,
            y=f_clean,
            mode="lines",
            name="Flux",
            line=dict(width=1.4),
            hovertemplate="<b>λ:</b> %{x:.1f} Å<br><b>Flux:</b> %{y:.2f}<extra></extra>",
        )
    )

    # Dynamic y-axis percentile limits to avoid spikes crushing the continuum
    y_min, y_max = None, None
    if len(f_clean) > 0:
        p_low, p_high = np.percentile(f_clean, [0.5, 99.5])
        flux_range = max(p_high - p_low, 1e-4)
        y_min = float(p_low - 0.08 * flux_range)
        y_max = float(p_high + 0.35 * flux_range)

    # Redshift & Line Markers
    z_val = obs.get("z")
    z_err = obs.get("z_err")
    z_str = ""
    if z_val is not None:
        if z_err is not None:
            z_str = f" | z = {z_val:.4f} ± {z_err:.4f}"
        else:
            z_str = f" | z = {z_val:.4f}"

        # Overlay redshifted lines as hoverable traces if inside observed spectral range
        if show_line_markers and len(w_clean) > 0:
            w_min, w_max = float(np.min(w_clean)), float(np.max(w_clean))
            y_bottom = y_min if y_min is not None else float(np.min(f_clean))
            y_top = y_max if y_max is not None else float(np.max(f_clean))

            for i, line_info in enumerate(REST_FRAME_LINES):
                obs_lambda = line_info["rest_wave"] * (1.0 + z_val)
                if w_min <= obs_lambda <= w_max:
                    fig.add_trace(
                        go.Scatter(
                            x=[obs_lambda, obs_lambda],
                            y=[y_bottom, y_top],
                            mode="lines",
                            name=line_info["name"],
                            line=dict(
                                color=line_info["color"],
                                width=1.3,
                                dash="dot",
                            ),
                            opacity=0.8,
                            hovertemplate=(
                                f"<b>{line_info['name']}</b><br>"
                                f"Rest λ: {line_info['rest_wave']:.2f} Å<br>"
                                f"Observed λ: {obs_lambda:.2f} Å"
                                "<extra></extra>"
                            ),
                            showlegend=False,
                        )
                    )
                    
                    # Alternate vertical position to prevent label overlap (zigzag)
                    y_pos = 0.98 if i % 2 == 0 else 0.88
                    
                    fig.add_annotation(
                        x=obs_lambda,
                        y=y_pos,
                        yref="paper",
                        text=line_info["name"],
                        showarrow=False,
                        xanchor="center",
                        yanchor="top",
                        textangle=-90,
                        font=dict(size=11, color=line_info["color"]),
                    )

    obs_str = f" (Obs {obs_index + 1}/{total_obs})" if total_obs > 1 else ""
    title_text = f"<b>{object_key}</b> [{dataset_source.upper()}]{obs_str}{z_str}"

    fig.update_layout(
        template="plotly",
        height=380,
        margin=dict(l=55, r=25, t=42, b=45),
        title=dict(
            text=title_text,
            font=dict(size=15),
            x=0.01,
            y=0.97,
        ),
        xaxis=dict(
            title=dict(text="Observed Wavelength (Å)", font=dict(size=13)),
            tickfont=dict(size=11),
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(
                text="Flux (10⁻¹⁷ erg s⁻¹ cm⁻² Å⁻¹)",
                font=dict(size=13),
            ),
            tickfont=dict(size=11),
            range=[y_min, y_max] if y_min is not None and y_max is not None else None,
            zeroline=False,
        ),
        hoverlabel=dict(
            font_size=12,
        ),
        showlegend=False,
        hovermode="x unified",
    )

    return fig
