from django import template
from django.conf import settings
from django.template import Context, Template
from decimal import Decimal

register = template.Library()

@register.simple_tag
def js_make_select_readonly(select):
    #This is really just a mini-template
    #select must be a jquery object
    return """
    select = %(select)s;
    value = select.attr("value");
    if (value){
        text = "";
        for (c in select.children()){
          if (select.children()[c].value == value){
            text = select.children()[c].innerHTML;
            break;
          }
        }
        select.before("<strong>" + text + "</strong><input type=\\"hidden\\" name=\\"" + select.attr("name") + "\\" value=\\"" + value + "\\" \>");
        select.remove();
    }
    """ % {'select':select}

@register.simple_tag
def edit_subtypes(product):
    output = '<ul>'
    for (app ,subtype) in settings.PRODUCT_TYPES:
        if subtype in product.get_subtypes():
            output += '<li><a href="/admin/%s/%s/%s/">Edit %s</a></li>'%(app, subtype.lower(), product.id, subtype)
        else:
            output += ' <li><a href="/admin/%s/%s/add/?product_id=%s">Add %s</a></li>'%(app, subtype.lower(), product.id, subtype)

    output += '</ul>'
    return output

@register.simple_tag
def list_variations(configurableproduct):
    opts = configurableproduct.get_all_options()
    output = "{% load admin_modify adminmedia %}"
    output += "<table>"
    for p_opt in opts:
        opt_strs = []
        [opt_strs.append(opt.name) for opt in p_opt]
        opt_str = ', '.join(opt_strs)

        product = configurableproduct.get_product_from_options(p_opt)
        if product:
            #TODO: What's the right way to get this URL?
            p_url = '/admin/product/product/%s/' % product.id
            pv_url = '/admin/product/productvariation/%s/' % product.id

            output += """
            <tr>
            <td>%s</td>
            <td><a href="%s">%s</a></td>
            <td><a class="deletelink" href="%sdelete/"> Delete ProductVariation</a></td>
            </tr>
            """ % (opt_str, p_url, product.name, pv_url)
        else:
            opt_ids = []
            [opt_ids.append(str(opt.id)) for opt in p_opt]
            opt_ids = ','.join(opt_ids)

            output += """
            <tr>
            <td>%s</td>
            <td/>
            <td><a href="../../productvariation/add/?parent_id=%s&options=%s" class="add-another" id="add_productvariation"> <img src="{%% admin_media_prefix %%}img/admin/icon_addlink.gif" width="10" height="10" alt="Add ProductVariation"/> Add Variation</a></td>
            </tr>
            """ % (opt_str, configurableproduct.product.id, opt_ids)
    output += "</table>"
    t = Template(output)
    return t.render(Context())
