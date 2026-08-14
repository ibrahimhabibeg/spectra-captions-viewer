import numpy as np
import plotly.graph_objects as go

# Common rest-frame emission lines (wavelength in Angstroms)
STANDARD_REST_LINES = [
    {"name": "[O II]", "lambda": 3728.80, "color": "#C4B5FD"},
    {"name": "Hβ", "lambda": 4862.68, "color": "#93C5FD"},
    {"name": "[O III]", "lambda": 5008.24, "color": "#6EE7B7"},
    {"name": "[N II]", "lambda": 6585.27, "color": "#FDE68A"},
    {"name": "Hα", "lambda": 6564.61, "color": "#FCA5A5"},
    {"name": "[S II]", "lambda": 6718.29, "color": "#FDBA74"},
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
        q1, q99 = np.percentile(f_clean, [0.5, 99.5])
        margin = (q99 - q1) * 0.12
        if margin > 0:
            y_min = float(q1 - margin)
            y_max = float(q99 + margin)

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

            for line_info in STANDARD_REST_LINES:
                obs_lambda = line_info["lambda"] * (1.0 + z_val)
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
                                f"Rest λ: {line_info['lambda']:.2f} Å<br>"
                                f"Observed λ: {obs_lambda:.2f} Å"
                                "<extra></extra>"
                            ),
                            showlegend=False,
                        )
                    )
                    fig.add_annotation(
                        x=obs_lambda,
                        y=1.0,
                        yref="paper",
                        text=line_info["name"],
                        showarrow=False,
                        xanchor="center",
                        yanchor="bottom",
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
