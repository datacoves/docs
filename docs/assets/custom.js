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
