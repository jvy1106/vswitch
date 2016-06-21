//vswitch object to talk to backend API
var vswitch = {
  //you might need to change the following line if you access outside of localhost
  vswitch_base_url: 'http://localhost:8888/v1/',

  toggle: function(env, toggle) {
    $.post(this.vswitch_base_url + 'vswitch', {'environment': env, 'toggle': toggle}, function(data) {
      location.reload();
    });
  },
};
