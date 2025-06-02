from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from enum import Enum

import pandas as pd
from django.db.models import Q


class InType(str, Enum):
    query = 0
    data_frame = 1


class MetricExprs(str, Enum):
    """List of Aggregation Functions(aggfunc) for pivot in Pandas"""

    COUNT = "count"
    NUNIQUE = "nunique"
    MIN = "min"
    MAX = "max"
    FIRST = "first"
    LAST = "last"
    UNIQUE = "unique"
    SDT = "sdt"
    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    VAR = "var"
    MAD = "mad"
    SKEW = "skew"
    SEM = "sem"
    QUANTILE = "quantile"


@dataclass
class Dimensions:
    fields: list[str]
    rename: dict = None


@dataclass
class Metric:
    expr: MetricExprs
    field: str
    _in: InType


@dataclass
class Filter:
    field: str
    exprs: str
    _in: InType
    value_types: list[object]


class ExprsFilterEnum(str, Enum):
    """List of conditional expressions within the filter"""

    EQ = "="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    BW = "between"
    EX = "except"
    CONTAINS = "contains"
    NCONTAINS = "ncontains"
    IANYOF = "isanyof"
    INONEOF = "isnoneof"
    IS = "is"
    IBF = "isbefore"
    IOOBF = "isonorbefore"
    IAT = "isafter"
    IOOAF = "isonorafter"
    IWITHIN = "iswithin"
    IEP = "isempty"

    # IEOF = "isexactof"
    # HANYOF = "hasanyof"
    # HALLOF = "hasallof"
    # HNONEOF = "hasnoneof"


EFE = ExprsFilterEnum


class BindingExprEnum(str, Enum):
    """List of condition bindings within the filter"""

    AND = "AND"
    OR = "OR"

    @classmethod
    def choices(cls):
        return [attr.value for attr in cls]


class ExprsDjangoFilter:
    """Handle and convert filter conditions into Django Q objects"""

    MAP_EXPRS = {
        EFE.GT.value: "gt",
        EFE.GTE.value: "gte",
        EFE.LT.value: "gt",
        EFE.LTE.value: "lte",
        EFE.CONTAINS.value: "icontains",
        EFE.IANYOF.value: "in",
        EFE.IBF.value: "lt",
        EFE.IOOBF.value: "lte",
        EFE.IAT.value: "gt",
        EFE.IOOAF.value: "gte",
        EFE.EQ.value: None,
        EFE.NEQ.value: None,
        EFE.NCONTAINS.value: None,
        EFE.INONEOF.value: None,
        EFE.IEP.value: None,
        EFE.IWITHIN.value: None,
        EFE.IS.value: None,
    }

    @classmethod
    def validate(cls, field, expr, value):
        if not all([expr in cls.MAP_EXPRS, field]):
            raise ValueError(f"Filters: {field} {expr} {value} - missed params")
        if expr in [EFE.GT, EFE.GTE, EFE.LT, EFE.LTE, EFE.CONTAINS, EFE.IBF, EFE.IOOBF, EFE.IAT, EFE.IOOAF, EFE.NEQ, EFE.NCONTAINS]:
            if type(value) not in [int, str]:
                raise ValueError(f"Filters: {field} {expr} {value} - Value must be an integer or string")
        if expr in [EFE.IANYOF, EFE.INONEOF, EFE.IWITHIN]:
            if not isinstance(value, list):
                raise ValueError(f"Filters: {field} {expr} {value} - Value must be a list")
            if expr in [EFE.IS, EFE.IWITHIN] and len(value) != 2:
                raise ValueError(f"Filters: {field} {expr} {value} - Value must be a two-element list")
        if expr in [EFE.IEP]:
            if value not in [0, 1]:
                raise ValueError(f"Filters: {field} {expr} {value} - Value must be 0 or 1")
        return cls.MAP_EXPRS.get(expr)

    # Chưa xác định: HANYOF, HALLOF
    @classmethod
    def q_object(cls, field, expr, value) -> (Q):
        map_expr = cls.validate(field, expr, value)
        if map_expr:
            q_expr = Q(**{f"{field}__{map_expr}": value})
        else:
            f_expr = getattr(cls, f"q_{EFE(expr).name}")
            q_expr = f_expr(field, value) if f_expr else Q()
        return q_expr

    @classmethod
    def q_EQ(cls, field, value):
        return Q(**{f"{field}": value})

    @classmethod
    def q_NEQ(cls, field, value):
        return ~Q(**{f"{field}": value})

    @classmethod
    def q_NCONTAINS(cls, field, value):
        return ~Q(**{f"{field}__icontains": value})

    @classmethod
    def q_INONEOF(cls, field, value):
        return ~Q(**{f"{field}__in": value})

    @classmethod
    def q_IEP(cls, field, value):
        return Q(**{f"{field}__isnull": bool(value)})

    @classmethod
    def q_IWITHIN(cls, field, value):
        return Q(**{f"{field}__gt": value[0], f"{field}__lt": value[-1]})

    @classmethod
    def q_IS(cls, field, value):
        return Q(**{f"{field}__gte": value[0], f"{field}__lte": value[-1]})


class ExprsDataFrameFilter:
    """Handle and convert filter conditions into string expressions for querying Pandas."""

    MAP_EXPRS = {
        EFE.EQ.value: "==",
        EFE.NEQ.value: "!=",
        EFE.LT.value: "<",
        EFE.LTE.value: "<=",
        EFE.GT.value: ">",
        EFE.GTE.value: ">=",
        EFE.BW.value: None,
        EFE.EX.value: None,
    }

    @classmethod
    def validate(cls, field, expr, value):
        if not all([expr in cls.MAP_EXPRS, field]):
            raise ValueError(f"Filters: {field} {expr} {value} - missed params")
        if expr in [EFE.GT, EFE.GTE, EFE.LT, EFE.LTE, EFE.NEQ]:
            if not isinstance(value, int):
                raise ValueError(f"Filters: {field} {expr} {value} - this value must be an integer")
        if expr in [EFE.BW, EFE.EX]:
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError(f"Filters: {field} {expr} {value} - Value must be a two-element list")
            for i in value:
                if not isinstance(i, int):
                    raise ValueError(f"Filters: {field} {expr} {value} - element in list must be an integer")
        return cls.MAP_EXPRS.get(expr)

    @classmethod
    def qr_str(cls, field, expr, value):
        map_expr = cls.validate(field, expr, value)
        if map_expr:
            expr_str = f"({field} {map_expr} {value})"
        else:
            f_expr = getattr(cls, f"qr_{EFE(expr).name}")
            expr_str = f"({f_expr(field, value)})" if f_expr else ""
        return expr_str

    @classmethod
    def qr_BW(cls, field, value):
        return f"{field} > {value[0]} and {field} < {value[-1]}"

    @classmethod
    def qr_EX(cls, field, value):
        return f"{field} < {value[0]} or {field} > {value[-1]}"


# pylint: disable=R0902
class PivotReportBase:
    """Pivot Report Base"""

    DIMS_AVB: dict[str, Dimensions] = {}
    METRICS_AVB: dict[str, Metric] = {}
    FILTERS_AVB: dict[str, Filter] = {}

    # pylint: disable=W1113
    def __init__(
        self,
        queryset,
        dimensions,
        metrics,
        filters=None,
        b_expr_dims: BindingExprEnum = BindingExprEnum.AND,
        b_expr_metrics: BindingExprEnum = BindingExprEnum.AND,
        *args,
        **kwargs,
    ):
        self.dimensions: dict = self._dimensions(dimensions)
        self.metrics: dict = self._metrics(metrics)

        self.filterset: Q = Q()
        self.df_filterset: list[str] = []
        self.b_expr_dims = b_expr_dims
        self.b_expr_metrics = b_expr_metrics
        self._parse_filter(filters)

        self.queryset = self._queryset(queryset)
        self._excute_filterset()

        self.df: pd.DataFrame = self._data_frame()
        self.pivot_table = self._pivot()
        self._excute_df_filterset()

        self.result = self._output()

    def _parse_filter(self, filters=None) -> (dict):
        if not filters:
            return None
        for filter in filters:
            name, expr, value = filter
            _filter: Filter = self.FILTERS_AVB.get(name)
            if (not _filter) or (expr not in _filter.exprs) or (type(value) not in _filter.value_types):
                raise ValueError(f"Filters: `['{name}', {expr}, {value}]` invalid")
            if _filter._in == InType.query:
                self._update_filterset(_filter.field, expr, value)
            else:
                self._update_df_filterset(_filter.field, expr, value)
        return filters

    def _update_filterset(self, field, expr, value):
        self.filterset.add(ExprsDjangoFilter.q_object(field, expr, value), self.b_expr_dims)

    def _update_df_filterset(self, field, expr, value):
        self.df_filterset.append(ExprsDataFrameFilter.qr_str(field, expr, value))

    def _excute_filterset(self):
        if isinstance(self.filterset, Q):
            self.queryset = self.queryset.filter(self.filterset)

    def _excute_df_filterset(self):
        if self.df_filterset:
            query_expr = f" {self.b_expr_metrics.lower()} ".join(self.df_filterset)
            self.pivot_table.query(query_expr, inplace=True)

    def _queryset(self, queryset):
        return queryset

    def _dimensions(self, dimensions: list[str]) -> (dict):
        _dimensions = {}
        for dims in dimensions:
            if dims not in dimensions:
                raise ValueError(f"Dimensions `{dims}` invalid")
            _dimensions[dims] = self.DIMS_AVB[dims]
        return _dimensions

    def _get_dimension_fields(self) -> (list):
        dimension_fields = []
        for dims in self.dimensions.values():
            dimension_fields.extend(dims.fields)
        return dimension_fields

    def _get_dimension_names(self) -> (list[str]):
        dimension_names = []
        for v in self.dimensions.values():
            if v.rename:
                dimension_names.extend(v.rename.values())
            else:
                dimension_names.extend(v.fields)
        return dimension_names

    def _metrics(self, metrics: list[str]) -> (dict):
        _metrics = {}
        for metric in metrics:
            if metric not in self.METRICS_AVB:
                raise ValueError(f"Metrics `{metric}` invalid")
            _metrics[metric] = self.METRICS_AVB[metric]
        return _metrics

    def _get_metric_fields(self, _in: InType = None) -> (list):
        metric_fields = []
        if _in:
            metric_fields = [metric.field for metric in self.metrics.values() if _in == metric._in]
        else:
            metric_fields = [metric.field for metric in self.metrics.values()]
        return metric_fields

    def _get_metric_names(self) -> (list[str]):
        return list(self.metrics.keys())

    def _get_metric_exprs(self) -> (dict):
        return {metric.field: metric.expr for metric in self.metrics.values()}

    def _data_frame(self):
        if not self.queryset:
            return pd.DataFrame()
        dims_fields = self._get_dimension_fields()
        fields_metrics = self._get_metric_fields(_in=InType.query)
        fields = dims_fields + fields_metrics
        return pd.DataFrame.from_dict(self.queryset.values(*fields))

    def _rename_pivot_table(self, pivot_table: pd.DataFrame) -> (pd.DataFrame):
        metrics_name = {value.field: key for key, value in self.metrics.items()}
        dims_name = {}
        for dimension in self.dimensions.values():
            if dimension.rename:
                dims_name.update(dimension.rename)
        # Trường hợp chỉ có 1 dimensions -> dims_name sẽ là chuỗi để phù hợp yêu cầu của hàm rename index data frame
        if len(dims_name) == 1 and len(list(pivot_table.index.names)) == 1:
            dims_name = list(dims_name.values())[0]
        if dims_name:
            pivot_table.rename(columns=metrics_name, inplace=True)
        if dims_name:
            pivot_table.index.rename(dims_name, inplace=True)
        return pivot_table

    def _pivot(self):
        if self.df.empty:
            return pd.DataFrame()
        pivot_table = self.df.pivot_table(
            index=self._get_dimension_fields(),
            values=self._get_metric_fields(),
            aggfunc=self._get_metric_exprs(),
            dropna=True,
            fill_value=0,
        )
        return self._rename_pivot_table(pivot_table)

    def _output(self, without_dimension=False):
        data_output = []
        if not self.pivot_table.empty:
            data_output = self.pivot_table.reset_index().to_dict(orient="records")
        return data_output

    @classmethod
    def help_text_dims(cls):
        return f"""<strong>Dimensions</strong>: <code>{list(cls.DIMS_AVB.keys())}</code> <br><strong>Ex</strong>: \
            `'['{list(cls.DIMS_AVB.keys())[0]}',]'`"""

    @classmethod
    def help_text_metrics(cls):
        return f"""<strong>Metrics</strong>: <code>{list(cls.METRICS_AVB.keys())}</code> <br><strong>\
            Ex</strong>: `'['{list(cls.METRICS_AVB.keys())[0]}']'`"""

    @classmethod
    def help_text_filters(cls):
        ft_doc = "<br>".join(
            [f"`{k}` - `{[e.value for e in v.exprs]}` - `{[t.__name__ for t in v.value_types]}`" for k, v in cls.FILTERS_AVB.items()]
        )
        return f"""
            <strong>Filters available:</strong><br>
            {ft_doc}<br>
            <strong>Ex</strong>: `'[['revenue', '>', 1000000],...]'`
        """


class PivotReportCompare:
    CREATED_DATE_F = "created_date"

    def __init__(
        self,
        first_created_date: list[datetime],
        second_created_date: list[datetime],
        first_inst: PivotReportBase,
        second_inst: PivotReportBase,
        dimensions: list[str],
    ):
        self.first_created_date = first_created_date
        self.second_created_date = second_created_date
        self.first_inst = first_inst
        self.second_inst = second_inst
        self.dimensions = dimensions
        self.dates: dict[datetime:datetime] = self._map_dates()
        self._dates_reverted = self._map_dates_reverted()

    def map_compare(self) -> (list[dict]):
        first_output = self.first_inst.result
        second_output = self._process_output_compare_object(self.second_inst.result)
        results = []

        # Join các record của table compare
        for record in first_output:
            record_date = record.get(self.CREATED_DATE_F)
            date_map = self.dates.get(record_date)
            obj_compare = second_output.pop(self._gen_unique_key_w_dim(record, created_date=date_map), {})
            if not obj_compare:
                obj_compare = self._get_default_record_values(data=record)
                obj_compare.update({self.CREATED_DATE_F: date_map})
            results.append({**record, "compare": obj_compare})
        # Thêm các record mới cho trường hợp chỉ có ở table compare
        for s_record in second_output.values():
            s_record_date = s_record.get(self.CREATED_DATE_F)
            obj_first = self._get_default_record_values(s_record)
            obj_first.update({self.CREATED_DATE_F: self._dates_reverted.get(s_record_date)})
            results.append({**obj_first, "compare": s_record})

        return results

    def _process_output_compare_object(self, data: dict) -> (dict):
        output = {self._gen_unique_key_w_dim(re): re for re in data}
        return output

    def _get_default_record_values(self, data: dict) -> (dict):
        return {dim: data.get(dim) for dim in self.dimensions}

    def _gen_unique_key_w_dim(self, _data: dict, *args, **kwargs) -> (str):
        values = {dim: str(_data.get(dim)) for dim in self.dimensions}
        values.update(kwargs)
        return "".join([str(v) for v in values.values()])

    def _map_dates(self) -> (dict[datetime:datetime]):
        dates = self._split_dates(*self.first_created_date)
        dates_cp = self._split_dates(*self.second_created_date)
        dates_map = dict(zip(dates, dates_cp))
        return dates_map

    def _map_dates_reverted(self) -> (dict[datetime:datetime]):
        return {v: k for k, v in self.dates.items()}

    def _split_dates(self, date_start, date_end) -> (list[datetime]):
        days = date_end - date_start
        dates = [date_start + timedelta(days=i) for i in range(0, days.days + 1)]
        return dates
