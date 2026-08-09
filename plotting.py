import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_spectrum(
    obs: dict,
    object_key: str,
    dataset_source: str,
    obs_index: int = 0,
    total_obs: int = 1,
) -> plt.Figure:
    """
    Generate a clean, high-quality Matplotlib figure of an astronomical spectrum.
    """
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=100)
    fig.patch.set_facecolor("#111827")  # Tailored dark theme background (gray-900)
    ax.set_facecolor("#1F2937")  # Gray-800 plot background

    if not obs or len(obs.get("lambda", [])) == 0:
        ax.text(
            0.5,
            0.5,
            "No Spectral Data Available",
            ha="center",
            va="center",
            color="#9CA3AF",
            fontsize=14,
        )
        ax.axis("off")
        return fig

    wavelength = np.array(obs["lambda"])
    flux = np.array(obs["flux"])
    ivar = np.array(obs.get("ivar", []))
    mask = np.array(obs.get("mask", []))

    # Filter out invalid wavelengths (<= 0)
    valid_indices = wavelength > 0

    # Filter out masked pixels if mask is provided
    if len(mask) == len(wavelength):
        # boolean mask: True indicates masked/bad pixel
        if mask.dtype == bool:
            valid_indices &= ~mask
        else:
            valid_indices &= mask == 0

    # Apply filter
    w_clean = wavelength[valid_indices]
    f_clean = flux[valid_indices]

    if len(w_clean) == 0:
        # Fallback to unfiltered if cleaning removed everything
        w_clean = wavelength
        f_clean = flux

    # Line plot with cyan/electric blue glow
    ax.plot(w_clean, f_clean, color="#38BDF8", linewidth=1.0, alpha=0.9, label="Flux")

    # Titles and Redshift information
    z_val = obs.get("z")
    z_err = obs.get("z_err")
    z_str = ""
    if z_val is not None:
        if z_err is not None:
            z_str = f" | z = {z_val:.4f} ± {z_err:.4f}"
        else:
            z_str = f" | z = {z_val:.4f}"

    obs_str = f" (Obs {obs_index + 1}/{total_obs})" if total_obs > 1 else ""
    title_text = (
        f"{object_key} [{dataset_source.upper()}]{obs_str}{z_str}\n"
        f"Object ID: {obs.get('object_id', 'N/A')}"
    )

    ax.set_title(title_text, color="#F9FAFB", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Observed Wavelength (Å)", color="#E5E7EB", fontsize=10, labelpad=8)
    ax.set_ylabel("Flux (10⁻¹⁷ erg s⁻¹ cm⁻² Å⁻¹)", color="#E5E7EB", fontsize=10, labelpad=8)

    # Styling grid, ticks, and spine colors
    ax.tick_params(colors="#9CA3AF", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#374151")

    ax.grid(True, linestyle="--", alpha=0.25, color="#6B7280")

    # Dynamic y-axis limits to avoid outlier spikes stretching the plot
    if len(f_clean) > 0:
        q1, q99 = np.percentile(f_clean, [0.5, 99.5])
        margin = (q99 - q1) * 0.1
        if margin > 0:
            ax.set_ylim(q1 - margin, q99 + margin)

    plt.tight_layout()
    return fig
