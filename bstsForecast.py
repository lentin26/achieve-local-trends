import tensorflow_probability as tfp
import tensorflow as tf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import ast


class bstsForecast:

    def __init__(self, n_steps=6):
        # forecast steps
        self.n_steps = n_steps
        # sampling function
        self.run_mcmc = tf.function(
            tfp.experimental.mcmc.windowed_adaptive_nuts,
            autograph=False, jit_compile=True
        )
        self.mcmc_samples = None
        self.sampler_stats = None
        self.forecast_dist = None
        # self.component_dists = None

        self.cache = {
            "skill_id": [],
            "forecast_date": [],
            "forecast_mean": [],
            "forecast_95_conf_upper": [],
            "forecast_95_conf_lower": []
        }

    def generate_bsts_model(self, observed=None):
        """
        Args:
        observed: Observed time series, tfp.sts use it to generate data informed prior.
        """
        # Trend
        trend = tfp.sts.LocalLinearTrend(observed_time_series=observed)
        # Seasonal
        seasonal = tfp.sts.Seasonal(num_seasons=12, observed_time_series=observed)
        # Full model
        return tfp.sts.Sum([trend, seasonal], observed_time_series=observed)

    def get_mcmc_samples(self, joint_distr):

        self.mcmc_samples, self.sampler_stats = self.run_mcmc(
            1000, joint_distr, n_chains=4, num_adaptation_steps=1000,
            seed=tf.constant([745678, 562345], dtype=tf.int32)
        )

    def get_forecast_dist(self, seq):
        """
        Fit bsts model to the observed
        """
        observed = tf.constant(seq, dtype=tf.float32)
        model = self.generate_bsts_model(observed=observed)

        model_jd = model.joint_distribution(observed_time_series=observed)
        self.get_mcmc_samples(model_jd)

        # Using a subset of posterior samples.
        parameter_samples = tf.nest.map_structure(lambda x: x[-100:, 0, ...], self.mcmc_samples)

        # Get forecast for n_steps.
        self.forecast_dist = tfp.sts.forecast(
            model,
            observed_time_series=observed,
            parameter_samples=parameter_samples,
            num_steps_forecast=self.n_steps)

    def forecast(self, skill_id, dates, seq):
        self.get_forecast_dist(seq)

        if not isinstance(dates, list):
            dates = list(dates)

        forecast_date = pd.date_range(
            start=dates[-1],
            end=dates[-1]  + np.timedelta64(self.n_steps, "M"),
            freq='MS')
        
        forecast_mean = np.squeeze(self.forecast_dist.mean())
        # correct first prediction to match observed
        forecast_mean = np.concatenate([
            [seq.tolist()[-1]], forecast_mean[1:] 
        ], axis=0)

        forecast_std = np.squeeze(self.forecast_dist.stddev())

        # update cache
        self.cache['skill_id'] += [skill_id] * len(forecast_date)
        self.cache['forecast_date'] += forecast_date.tolist()
        self.cache['forecast_mean'] += forecast_mean.tolist()
        self.cache['forecast_95_conf_upper'] += (forecast_mean - 1.96 * forecast_std).tolist()
        self.cache['forecast_95_conf_lower'] += (forecast_mean + 1.96 * forecast_std).tolist()



