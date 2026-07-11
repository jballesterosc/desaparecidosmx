"""Chart builders. Every figure follows docs/umbral-brand.md §6:
horizontal gridlines only, one series in signal, direct labels instead
of legend boxes, dotted stroke + labeled rule for the uncertain tail.
"""

import pandas as pd
import plotly.graph_objects as go

import data
import theme

# Months whose counts are still filling in at consultation time get the
# dotted "provisional" treatment. Six is a floor, not a promise — the
# register back-fills for years (docs/methodology.md); the window can be
# calibrated once snapshot vintages exist (DECISIONS.md #12.1).
PROVISIONAL_MONTHS = 6


def consult_month() -> str:
    return data.consultado_en()[:7]


def provisional_from() -> str:
    return str(pd.Period(consult_month(), "M") - PROVISIONAL_MONTHS)


def month_span(ini: str, fin: str) -> list[str]:
    """Calendar months ini..min(fin, consultation month). Months after
    the consultation cannot contain registered events and are not drawn."""
    fin = min(fin, consult_month())
    return [str(p) for p in pd.period_range(ini, fin, freq="M")]


def monthly_series(rows: pd.DataFrame, months: list[str]) -> pd.Series:
    """Sum per month over the span; absence of rows means zero."""
    return (
        rows.groupby("periodo")["conteo"].sum()
        .reindex(months, fill_value=0)
    )


def _split_provisional(serie: pd.Series) -> tuple[pd.Series, pd.Series]:
    """(solid, dotted) segments sharing the boundary point."""
    cut = provisional_from()
    solid = serie[serie.index <= cut]
    dotted = serie[serie.index >= cut]
    if solid.empty:          # whole range is provisional
        return serie.iloc[:0], serie
    return solid, dotted


def trend_fig(series: dict[str, tuple[pd.Series, str]]) -> go.Figure:
    """Line chart with per-series provisional tails.

    series maps a direct label -> (monthly Series, hex color). One of
    them must wear signal; the caller decides which.
    """
    fig = go.Figure()
    multi = len(series) > 1
    for label, (serie, color) in series.items():
        solid, dotted = _split_provisional(serie)
        hover = "%{x} · %{y:,.0f}<extra>" + label + "</extra>"
        if not solid.empty:
            fig.add_scatter(
                x=list(solid.index), y=solid.values, mode="lines",
                line=dict(color=color, width=2), name=label,
                hovertemplate=hover,
            )
        if len(dotted) > 1:
            fig.add_scatter(
                x=list(dotted.index), y=dotted.values, mode="lines",
                line=dict(color=color, width=2, dash="dot"), name=label,
                hovertemplate=hover,
            )
        if multi:  # direct label at the line's end — no legend box
            fig.add_annotation(
                x=serie.index[-1], y=float(serie.iloc[-1]),
                text=label, showarrow=False, xanchor="left", xshift=6,
                font=dict(family="IBM Plex Sans", size=12, color=color),
            )
    first = next(iter(series.values()))[0]
    cut = provisional_from()
    if first.index[0] <= cut <= first.index[-1]:
        # add_vline chokes on categorical x when it carries an
        # annotation; draw the rule and its label explicitly.
        fig.add_shape(
            type="line", x0=cut, x1=cut, y0=0, y1=1, yref="paper",
            line=dict(dash="dot", color=theme.MODE["caption"], width=1),
        )
        fig.add_annotation(
            x=cut, y=1, yref="paper", yanchor="bottom",
            text="provisional →", showarrow=False, xanchor="left",
            font=dict(family="IBM Plex Mono", size=11,
                      color=theme.MODE["caption"]),
        )
    fig.update_layout(**theme.plotly_layout())
    fig.update_layout(hovermode="x unified", height=380)
    fig.update_yaxes(tickformat="~s")
    n_months = len(first)
    fig.update_xaxes(
        tickmode="array",
        tickvals=[m for m in first.index if m.endswith("-01")]
        if n_months > 24 else None,
        ticktext=[m[:4] for m in first.index if m.endswith("-01")]
        if n_months > 24 else None,
        tickangle=0,
    )
    if multi:
        fig.update_layout(margin=dict(r=140))
    return fig
