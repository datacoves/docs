/*
 * Custom JS items for the site
 */

jQuery(document).ready(function() {
    // Slide reveal for sidebar.
    jQuery('div.sidebar-toggle-button').click(function(ev) {
        jQuery('body').toggleClass('close');
    });

    // Fix styles on sidebar -- everything gets 'file' by default
    jQuery('div.sidebar-nav ul').find('li').addClass('file');

    // But for li's containing ul's, that li gets 'folder' instead.
    jQuery('div.sidebar-nav ul').find('li > ul')
                                .parent()
                                .removeClass('file')
                                .addClass('folder');

    // Fix duplicate footer
    jQuery('footer').not('footer.keeper').remove();

    /*
     * Handle the sidebar 'ladder' correctly, popping out the items we
     * wish to see.
     *
     * Find the selected file by its href.
     */
    var selected_file = window.location.pathname.replaceAll('"', '\\"');

    // We want its parent li
    var selected_link = jQuery('div.sidebar-nav ul')
                            .find('a[href="' + selected_file + '"]')
                            .parent();

    // If we have something, add the proper classes to it.
    if (selected_link.length) {
        selected_link.addClass('active');

        if (selected_link.hasClass('folder')) {
            selected_link.addClass('open');
        }

        selected_link.parents('li').addClass('open');
    }

    // Update title
    var potential_titles = jQuery('li.active a');

    if (potential_titles.length) {
        jQuery('head title').text(
            'Datacoves Docs - ' + potential_titles.text()
        );
    }

    // Create a map of URLs to titles
    var titleMap = {};

    jQuery('div.sidebar-nav').find('a').each(function() {
        var jqThis = jQuery(this);
        titleMap[jqThis.attr('href')] = jqThis.text();
    });

    // Clear search
    jQuery('#searchbox').val('');

    // Set up search
    jQuery.ajax(
        '/assets/search-index.js',
        {
            dataType: 'text',
            method: 'GET',
            success: function (data) {
                var index = MiniSearch.loadJSON(data, {fields: ['text']});

                jQuery('#searchbox').on('input', function (ev) {
                    var results = index.search(
                        jQuery(this).val(),
                        {
                            prefix: true,
                            fuzzy: 0.3,
                        }
                    );

                    // Clear results div
                    var resultsDiv = jQuery('#resultsbox');
                    resultsDiv.empty();

                    // Take the first 10 results
                    for (var i = 0; i < results.length && (i < 10); i++) {
                        var newDiv = jQuery('<div class="matching-post"></div>');
                        var newA = jQuery('<a></a>');
                        var newH2 = jQuery('<h2></h2>');
                        var newP = jQuery('<p></p>');

                        if (titleMap[results[i].url]) {
                            newH2.html(titleMap[results[i].url]);
                        } else {
                            newH2.text("Datacoves Page");
                        }

                        // Add a snip
                        newP.html(
                            results[i].snip.substr(
                                results[i].snip.toLowerCase().indexOf(
                                    results[i].queryTerms[0].toLowerCase()
                                ),
                                50
                            )
                            +
                            "..."
                        );

                        newA.attr('href', results[i].url);

                        newA.append(newH2);
                        newA.append(newP);
                        newDiv.append(newA);
                        resultsDiv.append(newDiv);
                    }

                    resultsDiv.addClass('show');
                    jQuery('div.search').addClass('show');
                    jQuery('button.clear-button').addClass('show');
                });
            }
        }
    );

    // Handle clear button
    jQuery('button.clear-button').click(function (ev) {
        jQuery('#resultsbox').empty().removeClass('show');
        jQuery('div.search').removeClass('show');
        jQuery('button.clear-button').removeClass('show');
        jQuery('#searchbox').val('');;
    });
});

// Add edit on github support
function editOnGitHub()
{
    // What's our github URL?
    var url = 'https://github.com/datacoves/docs/edit/main/docs';

    url = url + window.location.pathname;

    // Is it a readme file?
    if (!window.location.pathname.endsWith('.html')) {
        url = url + 'README.md';
    } else {
        // replace .html with .md
        url = url.replace(/\.html$/, '.md')
    }

    window.open(url, '_blank');

    return false;
}
