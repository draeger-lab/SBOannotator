"""Template Manager for LLM-based SBO Annotation.

This module provides a template management system for loading and rendering
prompt templates used in LLM-based annotation.
"""

__author__ = 'Your Name'

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import jinja2


class TemplateManager:
    """Manager for loading and rendering templates for LLM prompts."""

    def __init__(self, templates_dir: Optional[str] = None) -> None:
        """Initialize the template manager.

        Args:
            templates_dir: Directory containing template files (default: 'templates')
        """
        # Use provided directory or default to a 'templates' directory
        self.templates_dir = templates_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'templates'
        )

        # Ensure templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)

        # Set up Jinja environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False
        )

        # Cache for loaded templates
        self._template_cache = {}

    def list_templates(self) -> list:
        """List available templates in the templates directory.

        Returns:
            List of template names
        """
        return [f for f in os.listdir(self.templates_dir)
                if f.endswith(('.txt', '.j2', '.jinja', '.tmpl'))]

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to use in template rendering

        Returns:
            The rendered template string

        Raises:
            FileNotFoundError: If the template doesn't exist
        """
        # Load template (with caching)
        if template_name not in self._template_cache:
            try:
                self._template_cache[template_name] = self.env.get_template(template_name)
            except jinja2.exceptions.TemplateNotFound:
                raise FileNotFoundError(f"Template not found: {template_name}")

        template = self._template_cache[template_name]

        # Render with provided context
        return template.render(**context)

    def load_template_from_string(self, template_string: str) -> jinja2.Template:
        """Load a template from a string.

        Args:
            template_string: The template string to load

        Returns:
            Jinja Template object
        """
        return self.env.from_string(template_string)

    def render_string_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string with the given context.

        Args:
            template_string: Template string to render
            context: Dictionary of variables to use in template rendering

        Returns:
            The rendered template string
        """
        template = self.load_template_from_string(template_string)
        return template.render(**context)

    def save_template(self, template_name: str, content: str) -> str:
        """Save a template to the templates directory.

        Args:
            template_name: Name to save the template as
            content: Template content

        Returns:
            Path to the saved template
        """
        # Add extension if not present
        if not any(template_name.endswith(ext) for ext in ('.txt', '.j2', '.jinja', '.tmpl')):
            template_name += '.j2'

        template_path = os.path.join(self.templates_dir, template_name)

        with open(template_path, 'w') as f:
            f.write(content)

        # Clear cache for this template if it exists
        if template_name in self._template_cache:
            del self._template_cache[template_name]

        return template_path

    def create_default_templates(self) -> None:
        """Create default templates if they don't exist."""
        # Define default templates for different reaction types
        default_templates = {
            'reaction_base.j2': """
You are a Systems Biology expert tasked with assigning SBO (Systems Biology Ontology) terms to biochemical reactions.

Reaction details:
- ID: {{ reaction.id }}
- Name: {{ reaction.name }}
- Reversible: {{ reaction.reversible }}
- Reactants: {{ reaction.reactants|join(', ') }}
- Products: {{ reaction.products|join(', ') }}
{% if reaction.ec_numbers %}
- EC Numbers: {{ reaction.ec_numbers|join(', ') }}
{% endif %}
{% if reaction.compartments %}
- Compartments: {{ reaction.compartments|join(', ') }}
{% endif %}

Relevant SBO terms include:
- SBO:0000176 (Biochemical reaction): General biochemical transformation
- SBO:0000200 (Redox reaction): Involves electron transfer (e.g., NAD/NADH)
- SBO:0000216 (Phosphorylation): Transfer of phosphate groups (look for ATP/ADP)
- SBO:0000655 (Transport reaction): Movement across compartments
- SBO:0000627 (Exchange reaction): Exchange with environment
- SBO:0000629 (Biomass production): Overall cell growth

Based on these details, what is the most appropriate SBO term for this reaction?
Provide your answer in JSON format with fields: sbo_term, confidence, explanation.
""",

            'transport_reaction.j2': """
You are a Systems Biology expert tasked with classifying transport reactions in the Systems Biology Ontology.

Transport Reaction details:
- ID: {{ reaction.id }}
- Name: {{ reaction.name }}
- Reversible: {{ reaction.reversible }}
- Reactants: {{ reaction.reactants|join(', ') }}
- Products: {{ reaction.products|join(', ') }}
- Source compartment: {{ reaction.source_compartment }}
- Target compartment: {{ reaction.target_compartment }}
{% if reaction.metabolites_transported %}
- Metabolites transported: {{ reaction.metabolites_transported|join(', ') }}
{% endif %}

Transport reaction SBO terms include:
- SBO:0000655 (Transport reaction): General transport
- SBO:0000657 (Active transport): Energy-requiring transport (ATP, GTP involved)
- SBO:0000658 (Passive transport): No energy required
- SBO:0000659 (Antiporter): Exchange of molecules in opposite directions
- SBO:0000660 (Symporter): Transport of molecules in same direction
- SBO:0000654 (Co-transport): Transport of multiple species

Based on these details, what is the most appropriate SBO term for this reaction?
Provide your answer in JSON format with fields: sbo_term, confidence, explanation.
""",

            'enzymatic_reaction.j2': """
You are a Systems Biology expert tasked with classifying enzymatic reactions using the Systems Biology Ontology.

Enzymatic Reaction details:
- ID: {{ reaction.id }}
- Name: {{ reaction.name }}
- EC Numbers: {{ reaction.ec_numbers|join(', ') }}
- Reversible: {{ reaction.reversible }}
- Reactants: {{ reaction.reactants|join(', ') }}
- Products: {{ reaction.products|join(', ') }}

Relevant SBO terms based on EC classification:
- SBO:0000200 (Oxidoreductase): EC 1.*
- SBO:0000402 (Transferase): EC 2.*
- SBO:0000376 (Hydrolase): EC 3.*
- SBO:0000211 (Lyase): EC 4.*
- SBO:0000377 (Isomerase): EC 5.*
- SBO:0000695 (Ligase): EC 6.*
- SBO:0000185 (Translocase): EC 7.*

More specific SBO terms include:
- SBO:0000216 (Phosphorylation): Transfer of phosphate groups
- SBO:0000217 (Glycosylation): Addition of glycosyl groups
- SBO:0000399 (Decarboxylation): Removal of carboxyl group
- SBO:0000400 (Decarbonylation): Removal of carbonyl group
- SBO:0000401 (Deamination): Removal of amino group

Based on these details, what is the most appropriate SBO term for this reaction?
Provide your answer in JSON format with fields: sbo_term, confidence, explanation.
""",

            'exchange_reaction.j2': """
You are a Systems Biology expert tasked with classifying exchange and boundary reactions in the Systems Biology Ontology.

Exchange Reaction details:
- ID: {{ reaction.id }}
- Name: {{ reaction.name }}
- Reversible: {{ reaction.reversible }}
- Reactants: {{ reaction.reactants|join(', ') }}
- Products: {{ reaction.products|join(', ') }}

Boundary reaction SBO terms include:
- SBO:0000627 (Exchange reaction): Exchange with environment (often prefixed with EX_)
- SBO:0000628 (Demand reaction): Pure consumption (often prefixed with DM_)
- SBO:0000632 (Sink reaction): Pure production (often prefixed with SK_)
- SBO:0000629 (Biomass production): Overall cell growth (contains "biomass" in name)
- SBO:0000630 (ATP energy): Non-growth associated maintenance

Based on these details, what is the most appropriate SBO term for this reaction?
Provide your answer in JSON format with fields: sbo_term, confidence, explanation.
"""
        }

        for template_name, content in default_templates.items():
            template_path = os.path.join(self.templates_dir, template_name)
            if not os.path.exists(template_path):
                with open(template_path, 'w') as f:
                    f.write(content.strip())

    def get_template_for_reaction(self, reaction_features: Dict[str, Any]) -> str:
        """Select the most appropriate template for a reaction based on its features.

        Args:
            reaction_features: Dictionary of reaction features

        Returns:
            Template name to use for this reaction
        """
        # Determine the appropriate template based on reaction features
        if 'exchange' in reaction_features.get('id', '').lower() or 'ex_' in reaction_features.get('id', '').lower():
            return 'exchange_reaction.j2'
        elif len(reaction_features.get('compartments', [])) > 1:
            return 'transport_reaction.j2'
        elif reaction_features.get('ec_numbers'):
            return 'enzymatic_reaction.j2'
        else:
            return 'reaction_base.j2'


# Example usage
if __name__ == "__main__":
    # Example usage
    template_manager = TemplateManager()

    # Create default templates if they don't exist
    template_manager.create_default_templates()

    print("Available templates:")
    for template in template_manager.list_templates():
        print(f"- {template}")

    # Example reaction features
    example_reaction = {
        "id": "R_GAPD",
        "name": "Glyceraldehyde-3-phosphate dehydrogenase",
        "reversible": True,
        "reactants": ["M_g3p_c", "M_nad_c", "M_pi_c"],
        "products": ["M_13dpg_c", "M_h_c", "M_nadh_c"],
        "ec_numbers": ["1.2.1.12"],
        "compartments": ["c"]
    }

    # Get appropriate template for this reaction
    template_name = template_manager.get_template_for_reaction(example_reaction)
    print(f"\nSelected template for reaction {example_reaction['id']}: {template_name}")

    # Example rendering (commented out since files might not exist yet)
    # rendered = template_manager.render_template(template_name, {"reaction": example_reaction})
    # print("\nRendered template:")
    # print(rendered)