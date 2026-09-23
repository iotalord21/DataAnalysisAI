from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np


class DataProfiler:
    """
    Automated dataset profiler producing deep descriptive statistics,
    outlier counts, categorical cardinality, and an LLM-optimized summary.
    """

    def profile_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_rows, total_cols = df.shape
        duplicate_rows = int(df.duplicated().sum())

        columns_profile = {}
        numeric_cols = []
        categorical_cols = []
        datetime_cols = []

        for col in df.columns:
            series = df[col]
            null_count = int(series.isnull().sum())
            null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

            # Determine column category
            if pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(col)
                clean_s = series.dropna()
                q1 = float(clean_s.quantile(0.25)) if len(clean_s) > 0 else 0.0
                q3 = float(clean_s.quantile(0.75)) if len(clean_s) > 0 else 0.0
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers_count = int(((clean_s < lower_bound) | (clean_s > upper_bound)).sum())

                columns_profile[col] = {
                    "type": "numeric",
                    "dtype": str(series.dtype),
                    "null_count": null_count,
                    "null_pct": null_pct,
                    "min": round(float(clean_s.min()), 4) if len(clean_s) > 0 else None,
                    "max": round(float(clean_s.max()), 4) if len(clean_s) > 0 else None,
                    "mean": round(float(clean_s.mean()), 4) if len(clean_s) > 0 else None,
                    "median": round(float(clean_s.median()), 4) if len(clean_s) > 0 else None,
                    "std": round(float(clean_s.std()), 4) if len(clean_s) > 1 else None,
                    "skew": round(float(clean_s.skew()), 4) if len(clean_s) > 2 else None,
                    "outliers_count": outliers_count,
                    "q1": round(q1, 4),
                    "q3": round(q3, 4),
                }
            elif pd.api.types.is_datetime64_any_dtype(series):
                datetime_cols.append(col)
                clean_s = series.dropna()
                columns_profile[col] = {
                    "type": "datetime",
                    "dtype": str(series.dtype),
                    "null_count": null_count,
                    "null_pct": null_pct,
                    "min": str(clean_s.min()) if len(clean_s) > 0 else None,
                    "max": str(clean_s.max()) if len(clean_s) > 0 else None,
                }
            else:
                categorical_cols.append(col)
                clean_s = series.dropna().astype(str)
                unique_count = int(clean_s.nunique())
                top_values = clean_s.value_counts().head(5).to_dict()
                top_vals_formatted = {
                    k: {"count": int(v), "pct": round((v / total_rows) * 100, 1)}
                    for k, v in top_values.items()
                }

                columns_profile[col] = {
                    "type": "categorical",
                    "dtype": str(series.dtype),
                    "null_count": null_count,
                    "null_pct": null_pct,
                    "unique_count": unique_count,
                    "top_values": top_vals_formatted,
                }

        # Calculate correlation matrix for numeric columns
        corr_matrix = {}
        high_correlations = []
        if len(numeric_cols) >= 2:
            corr_df = df[numeric_cols].corr()
            corr_matrix = corr_df.round(3).to_dict()

            # Extract noteworthy correlations (|r| >= 0.5, excluding diagonal)
            seen_pairs = set()
            for c1 in numeric_cols:
                for c2 in numeric_cols:
                    if c1 != c2 and (c2, c1) not in seen_pairs:
                        val = corr_df.loc[c1, c2]
                        if not np.isnan(val) and abs(val) >= 0.4:
                            high_correlations.append({
                                "var1": c1,
                                "var2": c2,
                                "correlation": round(float(val), 3),
                            })
                        seen_pairs.add((c1, c2))

        # Sort high correlations by absolute strength
        high_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        # Sample rows preview
        sample_records = df.head(5).replace({np.nan: None}).to_dict(orient="records")

        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "duplicate_rows": duplicate_rows,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols,
            "columns": columns_profile,
            "correlation_matrix": corr_matrix,
            "noteworthy_correlations": high_correlations[:10],
            "sample_rows": sample_records,
        }

    def profile_file(self, file_path: str) -> Dict[str, Any]:
        p = Path(file_path)
        if p.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(p)
        else:
            df = pd.read_csv(p)
        profile = self.profile_dataframe(df)
        profile["filename"] = p.name
        profile["file_size_bytes"] = p.stat().st_size
        return profile

    def format_for_prompt(self, profile: Dict[str, Any]) -> str:
        """
        Formats profile into a structured markdown overview for agent prompts.
        """
        lines = [
            f"### Dataset Overview: {profile.get('filename', 'Current Dataset')}",
            f"- **Dimensions**: {profile['total_rows']} rows × {profile['total_columns']} columns",
            f"- **Duplicates**: {profile['duplicate_rows']} rows",
            f"- **Numeric Columns ({len(profile['numeric_columns'])})**: {', '.join(profile['numeric_columns'])}",
            f"- **Categorical Columns ({len(profile['categorical_columns'])})**: {', '.join(profile['categorical_columns'])}",
        ]

        if profile["datetime_columns"]:
            lines.append(f"- **Datetime Columns**: {', '.join(profile['datetime_columns'])}")

        lines.append("\n#### Column Summary Statistics:")
        for col_name, stats in profile["columns"].items():
            if stats["type"] == "numeric":
                lines.append(
                    f"  - `{col_name}` (numeric): Min={stats['min']}, Max={stats['max']}, Mean={stats['mean']}, Median={stats['median']}, Std={stats['std']}, Outliers={stats['outliers_count']}, Missing={stats['null_pct']}%"
                )
            elif stats["type"] == "categorical":
                top_str = ", ".join([f"'{k}' ({v['count']})" for k, v in stats["top_values"].items()])
                lines.append(
                    f"  - `{col_name}` (categorical): {stats['unique_count']} unique values, Missing={stats['null_pct']}%. Top: [{top_str}]"
                )

        if profile.get("noteworthy_correlations"):
            lines.append("\n#### Strong Correlations (|r| >= 0.4):")
            for item in profile["noteworthy_correlations"]:
                lines.append(f"  - `{item['var1']}` ↔ `{item['var2']}`: r = {item['correlation']}")

        return "\n".join(lines)
