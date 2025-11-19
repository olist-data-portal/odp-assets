{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}
    {%- set prefix = var('dataset_prefix', 'dp') -%}
    {%- set env_name = target.name -%}

    {%- if custom_schema_name is none -%}

        {{ default_schema }}

    {%- else -%}

        {{ prefix }}_{{ env_name }}_{{ custom_schema_name | trim }}

    {%- endif -%}

{%- endmacro %}

